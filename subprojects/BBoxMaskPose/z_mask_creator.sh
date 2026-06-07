#!/bin/bash
set -e
# -----------------------------------------------------------------------------------------
# $ Usage: ./z_mask_creator.sh <image_name>
# $ Example: ./z_mask_creator.sh 00009.png
# -----------------------------------------------------------------------------------------
# Env
_env_name="${BMP_CONDA_ENV:-bbox_mask_pose}"
_py="${BMP_PYTHON:-${HOME}/miniconda3/envs/${_env_name}/bin/python}"
output_dir="${BMP_OUTPUT_DIR:-raw_mask}"
mkdir -p "${output_dir}"

# -----------------------------------------------------------------------------------------
# Input (DO NOT change name)
image_name="$1"
echo "[INFO] Processing image -> ${image_name}"
stem="$(basename "${image_name%.*}")"
image_path="${image_name}"

if [ ! -f "${image_path}" ]; then
  echo "[ERROR] input image not found: ${image_path}"
  exit 1
fi

# -----------------------------------------------------------------------------------------
# function 
get_max_iter_pre_mask() {
    local stem="$1"
    local dir="demo/outputs/${stem}"

    # iter1 一定存在
    local pre_mask="${dir}/${stem}_iter1_MaskPoseIn_Foreground_black.jpg"

    local i=2
    while true; do
        local candidate="${dir}/${stem}_iter${i}_MaskPoseIn_Foreground_black.jpg"
        if [[ -f "$candidate" ]]; then
            pre_mask="$candidate"
            ((i++))
        else
            break
        fi
    done

    echo "$pre_mask"
}

get_max_iter_ori_mask() {
    local stem="$1"
    local dir="demo/outputs/${stem}_mask"

    local ori_mask="${dir}/${stem}_mask_iter1_MaskPoseIn_Background.jpg"

    local i=2
    while true; do
        local candidate="${dir}/${stem}_mask_iter${i}_MaskPoseIn_Background.jpg"
        if [[ -f "$candidate" ]]; then
            ori_mask="$candidate"
            ((i++))
        else
            break
        fi
    done

    echo "$ori_mask"
}

# -----------------------------------------------------------------------------------------
# STEP 1: WHITE (default mode)
export BMP_BG_MODE=black

$_py demo/bmp_demo.py \
       configs/bmp_D3.yaml \
       "${image_path}"

temp="pre_mask_temp"
mkdir -p "${temp}"

pre_mask=$(get_max_iter_pre_mask "$stem")
echo "[INFO] Using highest iter pre_mask -> $pre_mask"

if [ ! -f "${pre_mask}" ]; then
  echo "[ERROR] pre_mask not found: ${pre_mask}"
  echo "[DEBUG] Existing files under demo/outputs/${stem}:"
  find "demo/outputs/${stem}" -maxdepth 1 -type f -printf "  %f\n" 2>/dev/null | sort || true
  exit 1
fi

mask="${temp}/${stem}_mask.jpg"
mv "${pre_mask}" "${mask}"


# -----------------------------------------------------------------------------------------
# STEP 2: BLACK (same input image)
export BMP_BG_MODE=white

$_py demo/bmp_demo.py \
       configs/bmp_D3.yaml \
       "$mask"

# -----------------------------------------------------------------------------------------
# Final mask comes from BLACK background
ori_mask_name=$(get_max_iter_ori_mask "$stem")
echo "[INFO] Using highest iter final mask -> $ori_mask_name"

final_mask_name="${output_dir}/${stem}_mask.jpg"

if [ ! -f "${ori_mask_name}" ]; then
  echo "[ERROR] final mask not found: ${ori_mask_name}"
  echo "[DEBUG] Existing files under demo/outputs/${stem}_mask:"
  find "demo/outputs/${stem}_mask" -maxdepth 1 -type f -printf "  %f\n" 2>/dev/null | sort || true
  exit 1
fi

mv "${ori_mask_name}" "${final_mask_name}"
echo "[DONE] final mask -> ${final_mask_name}"

# Remove temp files
rm -rf "${temp}"
rm -rf "demo/outputs/${stem}"
rm -rf "demo/outputs/${stem}_mask"
