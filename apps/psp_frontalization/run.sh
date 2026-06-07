#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${APP_DIR}/../.." && pwd)"
PSP_DIR="${PSP_DIR:-${REPO_ROOT}/subprojects/pixel2style2pixel}"

INPUT_DIR="${1:-${APP_DIR}/inputs}"
OUTPUT_DIR="${2:-${APP_DIR}/outputs}"

_env_name="${PSP_CONDA_ENV:-pixel2style2pixel}"
_env_dir="${HOME}/miniconda3/envs/${_env_name}"
_py="${PSP_PYTHON:-${_env_dir}/bin/python}"

CHECKPOINT="${PSP_CHECKPOINT:-${PSP_DIR}/pretrained_models/psp_ffhq_frontalization.pt}"
BATCH_SIZE="${PSP_BATCH_SIZE:-1}"
NUM_WORKERS="${PSP_NUM_WORKERS:-0}"
COUPLE_OUTPUTS="${PSP_COUPLE_OUTPUTS:---couple_outputs}"

if [[ ! -d "${PSP_DIR}" ]]; then
  echo "[ERROR] Missing pixel2style2pixel subproject: ${PSP_DIR}" >&2
  exit 1
fi

if [[ ! -x "${_py}" ]]; then
  echo "[ERROR] Missing python executable: ${_py}" >&2
  exit 1
fi

if [[ ! -f "${CHECKPOINT}" ]]; then
  echo "[ERROR] Missing pSp checkpoint: ${CHECKPOINT}" >&2
  exit 1
fi

if [[ ! -d "${INPUT_DIR}" ]]; then
  echo "[ERROR] Missing input dir: ${INPUT_DIR}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "[INFO] pSp dir    : ${PSP_DIR}"
echo "[INFO] input dir  : ${INPUT_DIR}"
echo "[INFO] output dir : ${OUTPUT_DIR}"
echo "[INFO] checkpoint : ${CHECKPOINT}"
echo "[INFO] python     : ${_py}"

(
  cd "${PSP_DIR}"
  env PATH="${_env_dir}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    "${_py}" scripts/inference.py \
      --exp_dir="${OUTPUT_DIR}" \
      --checkpoint_path="${CHECKPOINT}" \
      --data_path="${INPUT_DIR}" \
      --test_batch_size="${BATCH_SIZE}" \
      --test_workers="${NUM_WORKERS}" \
      ${COUPLE_OUTPUTS}
)

echo "[ALL DONE] pSp frontalization saved to: ${OUTPUT_DIR}"
