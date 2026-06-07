#!/usr/bin/env bash

# =========================
# Config
# =========================
EXP_DIR="experiments/psp_frontal_test"
CHECKPOINT="pretrained_models/psp_ffhq_frontalization.pt"
DATA_PATH="images/celeba_hq_male_gt"
BATCH_SIZE=1
NUM_WORKERS=0
COUPLE="--couple_outputs"


# =========================
# Run Inference
# =========================
python scripts/inference.py \
  --exp_dir="$EXP_DIR" \
  --checkpoint_path="$CHECKPOINT" \
  --data_path="$DATA_PATH" \
  --test_batch_size="$BATCH_SIZE" \
  --test_workers="$NUM_WORKERS" \
  $COUPLE


# =========================
# Output Structure
# =========================
# $EXP_DIR/
# ├── inference_results/
# ├── inference_coupled/
# └── stats.txt