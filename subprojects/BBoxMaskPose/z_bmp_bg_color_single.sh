#!/bin/bash
set -e

# -----------------------------------------------------------------------------------------
# Usage:
#   ./z_bmp_bg_color_single.sh <image_path> <mask_path> [output_dir]
#
# Example:
#   ./z_bmp_bg_color_single.sh \
#       /path/to/00001.png \
#       /path/to/00001_mask.png
# -----------------------------------------------------------------------------------------

_env_name="bbox_mask_pose"
_py="${HOME}/miniconda3/envs/${_env_name}/bin/python"


input_root="/mnt/d/Ph.D/01_Experiments_GAN_Inv_Log/2026.03.08_All_Experiments_Start/exper_06_psp_background_color_affect_face_fideility/single"
image_path="$input_root/blue_bg.png"
mask_path="$input_root/blue_mask.png"
output_dir="$input_root/output"

if [[ ! -f "${image_path}" ]]; then
    echo "[ERROR] image not found: ${image_path}"
    exit 1
fi

if [[ ! -f "${mask_path}" ]]; then
    echo "[ERROR] mask not found: ${mask_path}"
    exit 1
fi

export BMP_BG_BLUR_K="${BMP_BG_BLUR_K:-181}"
export BMP_BG_MODE_BINS="${BMP_BG_MODE_BINS:-32}"
export BMP_BG_MODE_SAMPLE_MAX="${BMP_BG_MODE_SAMPLE_MAX:-300000}"
export BMP_BG_RANDOM_SEED="${BMP_BG_RANDOM_SEED:-12345}"
export BMP_BG_ERODE_K="${BMP_BG_ERODE_K:-31}"

echo "[INFO] image     -> ${image_path}"
echo "[INFO] mask      -> ${mask_path}"
if [[ -n "${output_dir}" ]]; then
    echo "[INFO] output    -> ${output_dir}"
else
    echo "[INFO] output    -> <image_dir>/<image_stem>_bmp_bgcolor"
fi

cmd=(
    "${_py}"
    "z_bmp_bg_color_single.py"
    "${image_path}"
    "${mask_path}"
)

if [[ -n "${output_dir}" ]]; then
    cmd+=("--output-dir" "${output_dir}")
fi

"${cmd[@]}"
