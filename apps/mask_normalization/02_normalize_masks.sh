#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MASK_NORMALIZER="${APP_DIR}/mask_normalizer/mask_normalizer.py"

INPUT_DIR="${1:-${APP_DIR}/outputs/raw_masks}"
OUTPUT_DIR="${2:-${APP_DIR}/outputs/normalized_masks}"

_env_name="${MASK_NORMALIZER_CONDA_ENV:-seamless_clone}"
_py="${MASK_NORMALIZER_PYTHON:-${HOME}/miniconda3/envs/${_env_name}/bin/python}"

if [[ ! -f "${MASK_NORMALIZER}" ]]; then
  echo "[ERROR] Missing mask normalizer: ${MASK_NORMALIZER}" >&2
  exit 1
fi

if [[ ! -x "${_py}" ]]; then
  echo "[ERROR] Missing python executable: ${_py}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

mapfile -d '' -t masks < <(
  find "${INPUT_DIR}" -maxdepth 1 -type f \( \
    -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \
  \) -print0 | sort -z
)

if [[ "${#masks[@]}" -eq 0 ]]; then
  echo "[ERROR] No raw masks found: ${INPUT_DIR}" >&2
  exit 1
fi

echo "[INFO] Mask normalizer: ${MASK_NORMALIZER}"
echo "[INFO] Input dir      : ${INPUT_DIR}"
echo "[INFO] Normalized out : ${OUTPUT_DIR}"

for mask_path in "${masks[@]}"; do
  base="$(basename "${mask_path}")"
  stem="${base%.*}"
  out_path="${OUTPUT_DIR}/${stem}.png"

  echo "=============================================="
  echo "[RUN] ${base}"
  "${_py}" "${MASK_NORMALIZER}" \
    --in "${mask_path}" \
    --out "${out_path}" \
    --dilate 1
done

echo "[ALL DONE] Normalized masks saved to: ${OUTPUT_DIR}"
