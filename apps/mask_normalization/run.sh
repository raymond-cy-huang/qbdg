#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT_DIR="${1:-${APP_DIR}/inputs}"
RAW_MASK_DIR="${2:-${APP_DIR}/outputs/raw_masks}"
NORMALIZED_DIR="${3:-${APP_DIR}/outputs/normalized_masks}"

bash "${APP_DIR}/01_create_raw_masks.sh" "${INPUT_DIR}" "${RAW_MASK_DIR}"
bash "${APP_DIR}/02_normalize_masks.sh" "${RAW_MASK_DIR}" "${NORMALIZED_DIR}"
