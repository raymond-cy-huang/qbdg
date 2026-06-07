#!/usr/bin/env bash
set -euo pipefail

project_name="${1:-all}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

download_bbox_mask_pose() {
  local project_dir="${repo_root}/subprojects/BBoxMaskPose"
  local script="${repo_root}/setup/BBoxMaskPose/download_sam_ckpts.sh"
  local model_dir="${project_dir}/models/SAM"
  if [[ ! -d "${project_dir}" ]]; then
    echo "[ERROR] Missing project: ${project_dir}" >&2
    return 1
  fi

  if [[ ! -f "${script}" ]]; then
    echo "[ERROR] Missing script: ${script}" >&2
    return 1
  fi

  echo "[INFO] Downloading BBoxMaskPose SAM checkpoints"
  (
    mkdir -p "${model_dir}"
    cd "${model_dir}"
    bash "${script}"
  )
}

download_pixel2style2pixel() {
  local script="${repo_root}/setup/pixel2style2pixel/download_psp_models.sh"
  if [[ ! -f "${script}" ]]; then
    echo "[ERROR] Missing script: ${script}" >&2
    return 1
  fi

  bash "${script}"
}

case "${project_name}" in
  all)
    download_bbox_mask_pose
    download_pixel2style2pixel
    ;;
  BBoxMaskPose|bboxmaskpose|bbox_mask_pose)
    download_bbox_mask_pose
    ;;
  pixel2style2pixel|psp|pSp)
    download_pixel2style2pixel
    ;;
  *)
    echo "[ERROR] Unknown project: ${project_name}" >&2
    echo "Usage: bash setup/download_models.sh [all|BBoxMaskPose|pixel2style2pixel]" >&2
    exit 1
    ;;
esac
