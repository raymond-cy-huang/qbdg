# pSp Frontalization App

This app wraps `subprojects/pixel2style2pixel/scripts/inference.py` with the
FFHQ frontalization checkpoint.

## Run

```bash
bash apps/psp_frontalization/run.sh
```

Default paths:

- Inputs: `apps/psp_frontalization/inputs/`
- Outputs: `apps/psp_frontalization/outputs/`
- Checkpoint: `subprojects/pixel2style2pixel/pretrained_models/psp_ffhq_frontalization.pt`
- Conda env: `pixel2style2pixel`

Output folders:

- `inference_results/`: frontalized images.
- `inference_coupled/`: input/output side-by-side images.
- `stats.txt`: runtime summary.

Optional overrides:

```bash
PSP_BATCH_SIZE=1 PSP_NUM_WORKERS=0 bash apps/psp_frontalization/run.sh <input_dir> <output_dir>
```
