#!/usr/bin/env python3
# mask_normalizer.py
#
# Based on your workable mask_optimize_best_bbox.py, with:
# - boundary refinement (reduce halo): erode/close/open/dilate controls
# - supports --in as a file OR a sample directory containing mask.png
# - supports --out as a file OR output directory

import argparse
from pathlib import Path
import cv2
import numpy as np

IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def imread_any(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def to_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.ndim == 3:
        if img.shape[2] == 4:
            return img[:, :, :3]
        return img
    raise ValueError(f"Unsupported image shape: {img.shape}")


def whiteness_map(bgr: np.ndarray) -> np.ndarray:
    """
    Robust 'white-likeness' for bbox-style masks:
      score = min(B,G,R)  (white-ish requires all channels high)
    Better than grayscale when edges are color-contaminated.
    """
    b = bgr[:, :, 0].astype(np.uint16)
    g = bgr[:, :, 1].astype(np.uint16)
    r = bgr[:, :, 2].astype(np.uint16)
    return np.minimum(np.minimum(b, g), r).astype(np.uint8)


def percentile_contrast(x: np.ndarray, p_low=1.0, p_high=99.5) -> np.ndarray:
    xf = x.astype(np.float32)
    lo, hi = np.percentile(xf, (p_low, p_high))
    if hi <= lo + 1e-6:
        return x
    y = (xf - lo) * 255.0 / (hi - lo)
    return np.clip(y, 0, 255).astype(np.uint8)


def odd_at_least(v: int, mn: int = 3) -> int:
    v = int(v)
    v = max(v, mn)
    return v if v % 2 == 1 else v + 1


def auto_kernels(h: int, w: int):
    """
    Kernel sizing tuned for bbox masks: scale with min dimension.
    """
    m = min(h, w)
    k_open  = odd_at_least(int(m * 0.008), 3)   # remove speckles
    k_close = odd_at_least(int(m * 0.016), 5)   # fill edge gaps / eat fringes
    k_fill  = odd_at_least(int(m * 0.020), 7)   # stronger close if needed
    return k_open, k_close, k_fill


def largest_connected_component(mask_bin: np.ndarray) -> np.ndarray:
    """
    Keep the largest white component. Bbox masks typically contain one main blob.
    """
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask_bin, connectivity=8)
    if num <= 2:
        return mask_bin
    areas = stats[1:, cv2.CC_STAT_AREA]
    max_idx = 1 + int(np.argmax(areas))
    out = np.zeros_like(mask_bin)
    out[labels == max_idx] = 255
    return out


def optimize_bbox_mask(img: np.ndarray, invert: bool = False) -> np.ndarray:
    """
    Your original workable pipeline (kept), minus final dilation (we handle boundary later).
    """
    bgr = to_bgr(img)
    h, w = bgr.shape[:2]

    wmap = whiteness_map(bgr)
    wmap = percentile_contrast(wmap, 1.0, 99.5)
    wmap = cv2.medianBlur(wmap, 5)

    otsu_t, mask = cv2.threshold(wmap, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if otsu_t < 80:
        _, mask = cv2.threshold(wmap, 160, 255, cv2.THRESH_BINARY)

    if invert:
        mask = cv2.bitwise_not(mask)

    _, k_close, k_fill = auto_kernels(h, w)
    kernel_close = np.ones((k_close, k_close), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)

    mask = largest_connected_component(mask)

    area_ratio = mask.mean() / 255.0
    if 0.05 < area_ratio < 0.95:
        kernel_fill = np.ones((k_fill, k_fill), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_fill)

    mask = np.where(mask > 0, 255, 0).astype(np.uint8)
    return mask


def refine_boundary(
    mask_255: np.ndarray,
    open_k: int = 0,
    close_k: int = 0,
    erode_iter: int = 0,
    dilate_iter: int = 0,
) -> np.ndarray:
    """
    Boundary refinement to reduce halos / unnatural lighting artifacts.
    Most effective default for halo: erode_iter=1 (shrink mask slightly).
    """
    m = np.where(mask_255 > 0, 255, 0).astype(np.uint8)

    if open_k and open_k > 0:
        k = np.ones((odd_at_least(open_k), odd_at_least(open_k)), np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)

    if close_k and close_k > 0:
        k = np.ones((odd_at_least(close_k), odd_at_least(close_k)), np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)

    if erode_iter and erode_iter > 0:
        k = np.ones((3, 3), np.uint8)
        m = cv2.erode(m, k, iterations=int(erode_iter))

    if dilate_iter and dilate_iter > 0:
        k = np.ones((3, 3), np.uint8)
        m = cv2.dilate(m, k, iterations=int(dilate_iter))

    m = np.where(m > 0, 255, 0).astype(np.uint8)
    return m


def resolve_input(in_path: Path, mask_name: str) -> Path:
    """
    Accept:
      --in <file>
      --in <dir>  (then use <dir>/<mask_name>)
    """
    if in_path.is_dir():
        cand = in_path / mask_name
        if not cand.exists():
            raise ValueError(f"Cannot read src: {cand}")
        return cand
    if in_path.is_file():
        return in_path
    raise ValueError(f"Cannot read src: {in_path}")


def resolve_output(out_path: Path) -> Path:
    """
    If --out is a directory, output:
      <out>/mask.png
    If --out is a file, output:
      <out>.png
    """
    if out_path.suffix.lower() == "":
        out_dir = out_path
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / "mask.png"

    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Best mask normalizer for bbox-based masks (workable base + better boundary).")
    ap.add_argument("--in", dest="in_path", required=True, help="Input mask image OR sample directory containing mask.png.")
    ap.add_argument("--out", dest="out_path", required=True, help="Output directory OR output file base path.")
    ap.add_argument("--mask_name", default="mask.png", help="When --in is a directory, read this file. Default: mask.png")
    ap.add_argument("--invert", action="store_true", help="Invert final mask (swap black/white).")

    # Boundary controls (halo fix)
    ap.add_argument("--open", type=int, default=0, help="Morph OPEN kernel size (odd). 0=off.")
    ap.add_argument("--close", type=int, default=0, help="Morph CLOSE kernel size (odd). 0=off.")
    ap.add_argument("--erode", type=int, default=1, help="Erode iterations to shrink mask (halo fix). Default: 1")
    ap.add_argument("--dilate", type=int, default=0, help="Dilate iterations (expand mask). Default: 0")

    args = ap.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)

    src_mask_path = resolve_input(in_path, args.mask_name)
    mask_out = resolve_output(out_path)

    img = imread_any(src_mask_path)

    # Step 1: your original workable extraction
    mask = optimize_bbox_mask(img, invert=args.invert)

    # Step 2: boundary refinement (halo fix)
    mask = refine_boundary(
        mask,
        open_k=args.open,
        close_k=args.close,
        erode_iter=args.erode,
        dilate_iter=args.dilate,
    )

    if not cv2.imwrite(str(mask_out), mask):
        raise RuntimeError(f"Failed to write: {mask_out}")

    print(f"[OK] Saved mask: {mask_out}  unique={np.unique(mask).tolist()}")


if __name__ == "__main__":
    main()
