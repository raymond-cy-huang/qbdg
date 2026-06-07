#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT_DIR="$ROOT_DIR/inputs"
OUTPUT_DIR="$ROOT_DIR/outputs"
SCRIPT="$ROOT_DIR/mask_normalizer.py"

# sanity checks
if [ ! -f "$SCRIPT" ]; then
  echo "[ERROR] mask_normalizer.py not found at: $SCRIPT"
  exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
  echo "[ERROR] inputs/ directory not found at: $INPUT_DIR"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# collect files (robust, supports spaces)
mapfile -d '' -t FILES < <(
  find "$INPUT_DIR" -maxdepth 1 -type f \( \
    -iname "*.jpg"  -o -iname "*.jpeg" -o -iname "*.png"  -o -iname "*.webp" \
    -o -iname "*.bmp"  -o -iname "*.tif"  -o -iname "*.tiff" \
  \) -print0 | sort -z
)

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "[ERROR] No image files found in inputs/: $INPUT_DIR"
  echo "[HINT] Put files like *.jpg/*.png into inputs/ (not subfolders)."
  exit 1
fi

echo "Select an input mask:"
echo "---------------------"
for i in "${!FILES[@]}"; do
  echo "[$i] $(basename "${FILES[$i]}")"
done
echo

read -r -p "Enter index: " IDX

if ! [[ "$IDX" =~ ^[0-9]+$ ]] || [ "$IDX" -ge "${#FILES[@]}" ]; then
  echo "[ERROR] Invalid selection: $IDX"
  exit 1
fi

IN_PATH="${FILES[$IDX]}"
BASE="$(basename "$IN_PATH")"
STEM="${BASE%.*}"
OUT_PATH="$OUTPUT_DIR/$STEM.png"

echo
echo "[INFO] Input : $IN_PATH"
echo "[INFO] Output: $OUT_PATH"
echo

_env_name=seamless_clone
_py="${HOME}/miniconda3/envs/${_env_name}/bin/python"

$_py "$SCRIPT" \
  --in "$IN_PATH" \
  --out "$OUT_PATH" \
  --dilate 1

echo
echo "[DONE]"
