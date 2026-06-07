#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import cv2
import numpy as np


VALID_MODES = ("dark", "white", "mean", "median", "mode", "random", "gray", "blur")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create single-image background-color variants from an image and its mask."
    )
    parser.add_argument("image", type=Path, help="Path to the source image")
    parser.add_argument("mask", type=Path, help="Path to the foreground mask")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: <image_dir>/<image_stem>_bmp_bgcolor)",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=list(VALID_MODES),
        help="Background modes to export",
    )
    parser.add_argument("--blur-k", type=int, default=int(os.getenv("BMP_BG_BLUR_K", "181")))
    parser.add_argument("--mode-bins", type=int, default=int(os.getenv("BMP_BG_MODE_BINS", "32")))
    parser.add_argument(
        "--mode-sample-max",
        type=int,
        default=int(os.getenv("BMP_BG_MODE_SAMPLE_MAX", "300000")),
    )
    parser.add_argument("--random-seed", type=int, default=int(os.getenv("BMP_BG_RANDOM_SEED", "12345")))
    parser.add_argument("--erode-k", type=int, default=int(os.getenv("BMP_BG_ERODE_K", "31")))
    return parser.parse_args()


def ensure_odd(k: int, minimum: int = 3) -> int:
    return max(minimum, k | 1)


def load_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Failed to read image: {path}")
    return img


def load_mask(path: Path, shape_hw: tuple[int, int]) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if mask is None:
        raise FileNotFoundError(f"Failed to read mask: {path}")

    if mask.ndim == 3:
        if mask.shape[2] == 4:
            gray = mask[:, :, 3]
        else:
            gray = cv2.cvtColor(mask[:, :, :3], cv2.COLOR_BGR2GRAY)
    else:
        gray = mask

    if gray.shape[:2] != shape_hw:
        gray = cv2.resize(gray, (shape_hw[1], shape_hw[0]), interpolation=cv2.INTER_NEAREST)

    if gray.dtype != np.uint8:
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    return gray


def normalize_foreground_mask(mask_gray: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(mask_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    fg_mask = binary > 0

    if not fg_mask.any():
        raise ValueError("Mask is empty after thresholding.")

    h, w = fg_mask.shape
    cy1, cy2 = h // 4, max(h // 4 + 1, 3 * h // 4)
    cx1, cx2 = w // 4, max(w // 4 + 1, 3 * w // 4)

    center_score = int(fg_mask[cy1:cy2, cx1:cx2].sum())
    inv_center_score = int((~fg_mask)[cy1:cy2, cx1:cx2].sum())
    area_ratio = float(fg_mask.mean())

    if area_ratio > 0.7 or (area_ratio > 0.5 and center_score < inv_center_score):
        fg_mask = ~fg_mask

    return fg_mask


def erode_mask(mask_bool: np.ndarray, k: int) -> np.ndarray:
    k = ensure_odd(k)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    eroded = cv2.erode((mask_bool.astype(np.uint8) * 255), kernel, iterations=1) > 0
    if int(eroded.sum()) < 256:
        return mask_bool
    return eroded


def sample_bg_pixels(
    img_u8: np.ndarray,
    back_mask: np.ndarray,
    stat_mask: np.ndarray,
    sample_max: int,
) -> np.ndarray:
    bg_pixels = img_u8[stat_mask]
    if bg_pixels.size == 0:
        bg_pixels = img_u8[back_mask]
    if bg_pixels.size == 0:
        bg_pixels = img_u8.reshape(-1, 3)

    if bg_pixels.shape[0] > sample_max:
        stride = int(np.ceil(bg_pixels.shape[0] / sample_max))
        bg_pixels = bg_pixels[::stride]
    return bg_pixels.astype(np.uint8)


def closest_color_to_target(bg_pixels: np.ndarray, target_bgr: np.ndarray) -> np.ndarray:
    d2 = np.sum((bg_pixels.astype(np.int32) - target_bgr.astype(np.int32)) ** 2, axis=1)
    return bg_pixels[int(np.argmin(d2))]


def quantized_mode_color(bg_pixels: np.ndarray, bins: int) -> np.ndarray:
    bins = max(2, bins)
    q = (bg_pixels.astype(np.float32) * bins / 256.0).astype(np.int32)
    q = np.clip(q, 0, bins - 1)
    flat = q[:, 0] * bins * bins + q[:, 1] * bins + q[:, 2]
    mode_idx = int(np.bincount(flat).argmax())
    b = mode_idx // (bins * bins)
    g = (mode_idx // bins) % bins
    r = mode_idx % bins
    center = np.array([b, g, r], dtype=np.float32)
    return ((center + 0.5) * 256.0 / bins).clip(0, 255).astype(np.uint8)


def random_bg_color(bg_pixels: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return bg_pixels[int(rng.integers(0, len(bg_pixels)))]


def compose_variant(
    img_u8: np.ndarray,
    back_mask: np.ndarray,
    mode: str,
    bg_pixels: np.ndarray,
    blur_k: int,
    mode_bins: int,
    random_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    fg_img = img_u8.copy()

    if mode in ("dark", "white", "mean", "median", "mode", "random"):
        if mode == "dark":
            fill_bgr = closest_color_to_target(bg_pixels, np.array([0, 0, 0], dtype=np.uint8))
        elif mode == "white":
            fill_bgr = closest_color_to_target(bg_pixels, np.array([255, 255, 255], dtype=np.uint8))
        elif mode == "mean":
            fill_bgr = np.clip(bg_pixels.mean(axis=0), 0, 255).astype(np.uint8)
        elif mode == "median":
            fill_bgr = np.clip(np.median(bg_pixels, axis=0), 0, 255).astype(np.uint8)
        elif mode == "mode":
            fill_bgr = quantized_mode_color(bg_pixels, mode_bins)
        else:
            fill_bgr = random_bg_color(bg_pixels, random_seed)

        fg_img[back_mask] = fill_bgr
        return fg_img, fill_bgr

    if mode == "blur":
        blurred = cv2.GaussianBlur(img_u8, (ensure_odd(blur_k), ensure_odd(blur_k)), 0)
        fg_img[back_mask] = blurred[back_mask]
        return fg_img, np.array([-1, -1, -1], dtype=np.int32)

    gray1 = cv2.cvtColor(img_u8, cv2.COLOR_BGR2GRAY)
    gray3 = cv2.cvtColor(gray1, cv2.COLOR_GRAY2BGR)
    fg_img[back_mask] = gray3[back_mask]
    return fg_img, np.array([-1, -1, -1], dtype=np.int32)


def main() -> None:
    args = parse_args()

    image_path = args.image.expanduser().resolve()
    mask_path = args.mask.expanduser().resolve()

    img_u8 = load_image(image_path)
    mask_gray = load_mask(mask_path, img_u8.shape[:2])
    fore_mask = normalize_foreground_mask(mask_gray)
    back_mask = ~fore_mask

    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir is not None
        else image_path.parent / f"{image_path.stem}_bmp_bgcolor"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    stat_mask = erode_mask(back_mask, args.erode_k)
    bg_pixels = sample_bg_pixels(img_u8, back_mask, stat_mask, args.mode_sample_max)

    normalized_modes = []
    for mode in args.modes:
        mode_lower = mode.strip().lower()
        if mode_lower == "black":
            mode_lower = "dark"
        if mode_lower not in VALID_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        normalized_modes.append(mode_lower)

    mask_out = (fore_mask.astype(np.uint8) * 255)
    cv2.imwrite(str(output_dir / f"{image_path.stem}_mask.png"), mask_out)

    for mode in normalized_modes:
        out_img, fill_bgr = compose_variant(
            img_u8=img_u8,
            back_mask=back_mask,
            mode=mode,
            bg_pixels=bg_pixels,
            blur_k=args.blur_k,
            mode_bins=args.mode_bins,
            random_seed=args.random_seed,
        )

        out_path = output_dir / f"{image_path.stem}_{mode}.jpg"
        cv2.imwrite(str(out_path), out_img)

        if np.all(fill_bgr >= 0):
            info_path = output_dir / f"{image_path.stem}_{mode}_rgb.txt"
            info_path.write_text(
                "\n".join(
                    [
                        f"mode={mode}",
                        f"fill_bgr={fill_bgr.tolist()}",
                        f"N={int(bg_pixels.shape[0])}",
                        f"bins={args.mode_bins}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

        print(f"[OK] {out_path}")

    print(f"[DONE] Outputs -> {output_dir}")


if __name__ == "__main__":
    main()
