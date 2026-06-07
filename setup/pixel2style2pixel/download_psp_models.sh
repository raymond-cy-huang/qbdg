#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
project_dir="${repo_root}/subprojects/pixel2style2pixel"
model_dir="${project_dir}/pretrained_models"

mkdir -p "${model_dir}"

download_google_drive_file() {
  local file_id="$1"
  local output_path="$2"

  if [[ -s "${output_path}" ]]; then
    echo "[SKIP] Existing model: ${output_path}"
    return
  fi

  echo "[INFO] Downloading ${output_path}"
  wget --load-cookies /tmp/qbdg_psp_cookies.txt \
    "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/qbdg_psp_cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=${file_id}" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=${file_id}" \
    -O "${output_path}"
  rm -f /tmp/qbdg_psp_cookies.txt
}

download_google_drive_file "1_S4THAzXb-97DbpXmanjHtXRyKxqjARv" "${model_dir}/psp_ffhq_frontalization.pt"

shape_predictor="${model_dir}/shape_predictor_68_face_landmarks.dat"
if [[ -s "${shape_predictor}" ]]; then
  echo "[SKIP] Existing model: ${shape_predictor}"
else
  echo "[INFO] Downloading ${shape_predictor}"
  wget -O "${shape_predictor}.bz2" http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
  bunzip2 -f "${shape_predictor}.bz2"
fi

echo "[DONE] pixel2style2pixel models are ready in ${model_dir}"
