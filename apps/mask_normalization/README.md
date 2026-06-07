# Mask Normalization App

This downstream app uses only the research pipeline pieces needed for mask normalization:

- `subprojects/BBoxMaskPose/z_mask_creator.sh` creates raw BBoxMaskPose masks.
- `apps/mask_normalization/mask_normalizer/mask_normalizer.py` converts raw masks into normalized masks.

## Run

```bash
bash apps/mask_normalization/run.sh
```

Default paths:

- Input images: `apps/mask_normalization/inputs/`
- Raw masks: `apps/mask_normalization/outputs/raw_masks/`
- Normalized masks: `apps/mask_normalization/outputs/normalized_masks/`

You can also pass explicit paths:

```bash
bash apps/mask_normalization/run.sh <input_dir> <raw_mask_dir> <normalized_mask_dir>
```
