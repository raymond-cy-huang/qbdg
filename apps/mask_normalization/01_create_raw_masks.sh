#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${APP_DIR}/../.." && pwd)"
BBOX_MASK_POSE_DIR="${BBOX_MASK_POSE_DIR:-${REPO_ROOT}/subprojects/BBoxMaskPose}"

INPUT_DIR="${1:-${APP_DIR}/inputs}"
OUTPUT_DIR="${2:-${APP_DIR}/outputs/raw_masks}"

if [[ ! -x "${BBOX_MASK_POSE_DIR}/z_mask_creator.sh" ]]; then
  chmod +x "${BBOX_MASK_POSE_DIR}/z_mask_creator.sh"
fi

mkdir -p "${OUTPUT_DIR}"

mapfile -d '' -t images < <(
  find "${INPUT_DIR}" -maxdepth 1 -type f \( \
    -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" \
  \) -print0 | sort -z
)

if [[ "${#images[@]}" -eq 0 ]]; then
  echo "[ERROR] No input images found: ${INPUT_DIR}" >&2
  exit 1
fi

echo "[INFO] BBoxMaskPose: ${BBOX_MASK_POSE_DIR}"
echo "[INFO] Input dir   : ${INPUT_DIR}"
echo "[INFO] Raw mask out: ${OUTPUT_DIR}"

for image_path in "${images[@]}"; do
  image_name="$(basename "${image_path}")"
  echo "=============================================="
  echo "[RUN] ${image_name}"
  (
    cd "${BBOX_MASK_POSE_DIR}"
    BMP_OUTPUT_DIR="${OUTPUT_DIR}" \
    ./z_mask_creator.sh "${image_path}"
  )
done

echo "[ALL DONE] Raw masks saved to: ${OUTPUT_DIR}"
