#!/usr/bin/env bash
set -euo pipefail

_env_name=seamless_clone
_py="${HOME}/miniconda3/envs/${_env_name}/bin/python"

# ----------------------------
INPUT_DIR="/mnt/d/Ph.D/01_Experiments_GAN_Inv_Log/2026.03.08_All_Experiments_Start/exper_05_psp_face_frontal_analysis/male_mask"
OUTPUT_DIR="/mnt/d/Ph.D/01_Experiments_GAN_Inv_Log/2026.03.08_All_Experiments_Start/exper_05_psp_face_frontal_analysis/male_mask_normalized"
SCRIPT="mask_normalizer.py"
# ----------------------------

# 建立 output folder（若不存在）
mkdir -p "$OUTPUT_DIR"

echo "[INFO] Input Dir : $INPUT_DIR"
echo "[INFO] Output Dir: $OUTPUT_DIR"
echo

# 逐一處理 input folder 內所有圖片
find "$INPUT_DIR" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.webp" \) | while read -r IN_PATH; do

  BASE="$(basename "$IN_PATH")"
  STEM="${BASE%.*}"
  OUT_PATH="$OUTPUT_DIR/$STEM.png"

  echo "=============================================="
  echo "[INFO] Input : $IN_PATH"
  echo "[INFO] Output: $OUT_PATH"

  "$_py" "$SCRIPT" \
    --in "$IN_PATH" \
    --out "$OUT_PATH" \
    --dilate 1

  echo "[DONE] $BASE"
  echo
done

echo "[ALL DONE]"