#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


DEFAULT_MODES = ["original", "dark", "white", "mean", "median", "mode", "random", "gray", "blur"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create per-image background transformation diagnostic sheets.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--modes", nargs="+", default=DEFAULT_MODES)
    parser.add_argument("--panel-size", type=int, default=180)
    return parser.parse_args()


def image_paths(input_dir: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in exts and not p.stem.endswith("_mask")
    )


def labeled_panel(img: np.ndarray, label: str, size: int) -> np.ndarray:
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    label_bar = np.full((34, size, 3), 255, dtype=np.uint8)
    cv2.putText(label_bar, label, (6, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    return np.vstack([label_bar, img])


def placeholder(label: str, size: int) -> np.ndarray:
    img = np.full((size, size, 3), 245, dtype=np.uint8)
    cv2.putText(img, "missing", (18, size // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 180), 2, cv2.LINE_AA)
    return labeled_panel(img, label, size)


def main() -> None:
    args = parse_args()
    for image_path in image_paths(args.input_dir):
        stem = image_path.stem
        output_subdir = args.output_dir / stem
        panels = []

        for mode in args.modes:
            if mode == "original":
                path = image_path
                label = "original"
            else:
                path = output_subdir / f"{stem}_{mode}.jpg"
                label = mode

            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            panels.append(placeholder(label, args.panel_size) if img is None else labeled_panel(img, label, args.panel_size))

        sheet = np.hstack(panels)
        output_subdir.mkdir(parents=True, exist_ok=True)
        out_path = output_subdir / f"{stem}_diagnostic.jpg"
        cv2.imwrite(str(out_path), sheet)
        print(f"[OK] {out_path}")


if __name__ == "__main__":
    main()
