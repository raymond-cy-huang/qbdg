#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${APP_DIR}/../.." && pwd)"

INPUT_DIR="${1:-${APP_DIR}/inputs}"
MASK_DIR="${2:-${INPUT_DIR}}"
OUTPUT_DIR="${3:-${APP_DIR}/outputs}"

_env_name="${BACKGROUND_TRANSFORM_CONDA_ENV:-seamless_clone}"
_py="${BACKGROUND_TRANSFORM_PYTHON:-${HOME}/miniconda3/envs/${_env_name}/bin/python}"
SCRIPT="${APP_DIR}/background_transform.py"

read -r -a MODES <<< "${BG_TRANSFORM_MODES:-dark white mean median mode random gray blur}"

if [[ ! -x "${_py}" ]]; then
  echo "[ERROR] Missing python executable: ${_py}" >&2
  exit 1
fi

if [[ ! -f "${SCRIPT}" ]]; then
  echo "[ERROR] Missing transform script: ${SCRIPT}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

mapfile -d '' -t images < <(
  find "${INPUT_DIR}" -maxdepth 1 -type f \( \
    -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \
  \) ! -iname "*_mask.*" -print0 | sort -z
)

if [[ "${#images[@]}" -eq 0 ]]; then
  echo "[ERROR] No input images found: ${INPUT_DIR}" >&2
  exit 1
fi

resolve_mask() {
  local stem="$1"
  local exact="${MASK_DIR}/${stem}_mask.png"
  if [[ -f "${exact}" ]]; then
    echo "${exact}"
    return
  fi

  local same_stem="${MASK_DIR}/${stem}.png"
  if [[ -f "${same_stem}" ]]; then
    echo "${same_stem}"
    return
  fi

  return 1
}

echo "[INFO] Transform script: ${SCRIPT}"
echo "[INFO] Input dir       : ${INPUT_DIR}"
echo "[INFO] Mask dir        : ${MASK_DIR}"
echo "[INFO] Output dir      : ${OUTPUT_DIR}"
echo "[INFO] Modes           : ${MODES[*]}"

for image_path in "${images[@]}"; do
  base="$(basename "${image_path}")"
  stem="${base%.*}"

  if ! mask_path="$(resolve_mask "${stem}")"; then
    echo "[ERROR] No mask found for ${base} in ${MASK_DIR}" >&2
    exit 1
  fi

  out_dir="${OUTPUT_DIR}/${stem}"

  echo "=============================================="
  echo "[RUN] image: ${image_path}"
  echo "[RUN] mask : ${mask_path}"
  echo "[RUN] out  : ${out_dir}"

  "${_py}" "${SCRIPT}" \
    "${image_path}" \
    "${mask_path}" \
    --output-dir "${out_dir}" \
    --modes "${MODES[@]}"
done

echo "[ALL DONE] Background transformations saved to: ${OUTPUT_DIR}"

"${_py}" "${APP_DIR}/make_diagnostics.py" \
  --input-dir "${INPUT_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --modes original "${MODES[@]}"
