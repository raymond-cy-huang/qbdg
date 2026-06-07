#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT_DIR="${1:-${APP_DIR}/inputs}"
OUTPUT_DIR="${2:-${APP_DIR}/outputs}"

_env_name="${PSP_IOU_CONDA_ENV:-seamless_clone}"
_py="${PSP_IOU_PYTHON:-${HOME}/miniconda3/envs/${_env_name}/bin/python}"

GT_PATH="${GT_PATH:-${INPUT_DIR}/gt.jpg}"
GT_MASK_PATH="${GT_MASK_PATH:-${INPUT_DIR}/gt_mask.png}"
PSP_PATH="${PSP_PATH:-${INPUT_DIR}/psp_front.jpg}"
PSP_MASK_PATH="${PSP_MASK_PATH:-${INPUT_DIR}/psp_front_mask.jpg}"

if [[ ! -x "${_py}" ]]; then
  echo "[ERROR] Missing python executable: ${_py}" >&2
  exit 1
fi

for path in "${GT_PATH}" "${GT_MASK_PATH}" "${PSP_PATH}" "${PSP_MASK_PATH}"; do
  if [[ ! -f "${path}" ]]; then
    echo "[ERROR] Missing input: ${path}" >&2
    exit 1
  fi
done

mkdir -p "${OUTPUT_DIR}"

"${_py}" "${APP_DIR}/mask_iou_drawer.py" \
  --gt "${GT_PATH}" \
  --gt-mask "${GT_MASK_PATH}" \
  --psp "${PSP_PATH}" \
  --psp-mask "${PSP_MASK_PATH}" \
  --output-dir "${OUTPUT_DIR}"
