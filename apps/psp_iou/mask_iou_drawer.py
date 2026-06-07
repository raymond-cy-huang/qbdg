#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


YELLOW = (0, 255, 255)
RED = (0, 0, 255)
PURPLE = (255, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw GT/pSp background-mask IoU overlays.")
    parser.add_argument("--gt", type=Path, required=True, help="GT image.")
    parser.add_argument("--gt-mask", type=Path, required=True, help="GT foreground mask, white foreground / black background.")
    parser.add_argument("--psp", type=Path, required=True, help="pSp frontalized image.")
    parser.add_argument("--psp-mask", type=Path, required=True, help="pSp foreground mask, white foreground / black background.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=int, default=127)
    parser.add_argument("--gt-border", type=int, default=10)
    parser.add_argument("--psp-border", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--show-text", action="store_true")
    return parser.parse_args()


def load_image(path: Path, mode: int = cv2.IMREAD_COLOR) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    img = cv2.imread(str(path), mode)
    if img is None:
        raise RuntimeError(f"Read failed: {path}")
    return img


def background_mask(mask_img: np.ndarray, threshold: int) -> np.ndarray:
    """Convert a foreground mask to a binary background mask.

    The mask convention in this app is white foreground / black background.
    Therefore dark pixels are treated as the background region for IoU.
    """

    gray = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY) if mask_img.ndim == 3 else mask_img
    _, binary_bg = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    return binary_bg


def resize_mask(mask: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    h, w = hw
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)


def resize_image(img: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    h, w = hw
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)


def compute_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> tuple[float, int, int]:
    a = mask_a > 0
    b = mask_b > 0
    intersection = int(np.logical_and(a, b).sum())
    union = int(np.logical_or(a, b).sum())
    return (0.0 if union == 0 else float(intersection / union), intersection, union)


def make_outer_border(mask: np.ndarray, thickness: int) -> np.ndarray:
    kernel_size = thickness * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated = cv2.dilate(mask, kernel, iterations=1)
    return cv2.subtract(dilated, mask)


def paint_binary_region(img: np.ndarray, binary_mask: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    out = img.copy()
    out[binary_mask > 0] = color
    return out


def fill_mask_overlay(img: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    out = img.copy()
    color_layer = np.zeros_like(img, dtype=np.uint8)
    color_layer[:] = color
    mask_bool = mask > 0
    out[mask_bool] = cv2.addWeighted(img[mask_bool], 1 - alpha, color_layer[mask_bool], alpha, 0)
    return out


def put_iou_text(img: np.ndarray, iou: float, intersection: int, union: int) -> np.ndarray:
    out = img.copy()
    text = f"Background IoU: {iou:.4f}  Int: {intersection}  Union: {union}"
    pos = (30, 70)
    cv2.putText(out, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.4, BLACK, 7, cv2.LINE_AA)
    cv2.putText(out, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 1.4, WHITE, 3, cv2.LINE_AA)
    return out


def save(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), img):
        raise RuntimeError(f"Failed to write: {path}")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    gt = load_image(args.gt)
    psp = load_image(args.psp)
    gt_mask_img = load_image(args.gt_mask)
    psp_mask_img = load_image(args.psp_mask)

    h, w = gt.shape[:2]
    if psp.shape[:2] != (h, w):
        psp = resize_image(psp, (h, w))

    gt_bg = background_mask(gt_mask_img, args.threshold)
    psp_bg = background_mask(psp_mask_img, args.threshold)
    if gt_bg.shape[:2] != (h, w):
        gt_bg = resize_mask(gt_bg, (h, w))
    if psp_bg.shape[:2] != (h, w):
        psp_bg = resize_mask(psp_bg, (h, w))

    intersection_mask = cv2.bitwise_and(gt_bg, psp_bg)
    iou, intersection, union = compute_iou(gt_bg, psp_bg)

    gt_outer_border = make_outer_border(gt_bg, args.gt_border)
    psp_outer_border = make_outer_border(psp_bg, args.psp_border)

    gt_mask_border = paint_binary_region(gt_mask_img if gt_mask_img.ndim == 3 else cv2.cvtColor(gt_mask_img, cv2.COLOR_GRAY2BGR), gt_outer_border, YELLOW)
    psp_mask_border = paint_binary_region(psp_mask_img if psp_mask_img.ndim == 3 else cv2.cvtColor(psp_mask_img, cv2.COLOR_GRAY2BGR), psp_outer_border, RED)

    gt_overlay = fill_mask_overlay(gt, intersection_mask, PURPLE, args.alpha)
    gt_overlay = paint_binary_region(gt_overlay, gt_outer_border, YELLOW)
    gt_overlay = paint_binary_region(gt_overlay, psp_outer_border, RED)

    psp_overlay = fill_mask_overlay(psp, intersection_mask, PURPLE, args.alpha)
    psp_overlay = paint_binary_region(psp_overlay, gt_outer_border, YELLOW)
    psp_overlay = paint_binary_region(psp_overlay, psp_outer_border, RED)

    if args.show_text:
        gt_overlay = put_iou_text(gt_overlay, iou, intersection, union)
        psp_overlay = put_iou_text(psp_overlay, iou, intersection, union)

    canvas = np.vstack([np.hstack([gt_mask_border, psp_mask_border]), np.hstack([gt_overlay, psp_overlay])])
    if args.show_text:
        canvas = put_iou_text(canvas, iou, intersection, union)

    save(args.output_dir / "01_gt_mask_yellow_background_border.png", gt_mask_border)
    save(args.output_dir / "02_psp_mask_red_background_border.png", psp_mask_border)
    save(args.output_dir / "03_gt_with_background_iou_overlay.png", gt_overlay)
    save(args.output_dir / "04_psp_with_background_iou_overlay.png", psp_overlay)
    save(args.output_dir / "00_summary_2x2_background_iou.png", canvas)

    with (args.output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["background_iou", "intersection_pixels", "union_pixels"])
        writer.writeheader()
        writer.writerow(
            {
                "background_iou": f"{iou:.8f}",
                "intersection_pixels": intersection,
                "union_pixels": union,
            }
        )

    print(f"Background IoU : {iou:.6f}")
    print(f"Intersection   : {intersection}")
    print(f"Union          : {union}")
    print(f"Saved results  : {args.output_dir}")


if __name__ == "__main__":
    main()
