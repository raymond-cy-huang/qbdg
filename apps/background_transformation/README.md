# Background Transformation App

This app ports the former BBoxMaskPose background-color transformation logic into
an app-local script so it does not depend on switching the BBoxMaskPose branch
used by `apps/mask_normalization`.

## Inputs

- Images: `apps/background_transformation/inputs/`
- Masks: defaults to `apps/background_transformation/inputs/`

Mask lookup order for each `<image_stem>`:

1. `<image_stem>_mask.png`
2. `<image_stem>.png`

Mask files in the input directory are ignored as source images.

## Run

```bash
bash apps/background_transformation/run.sh
```

Explicit paths:

```bash
bash apps/background_transformation/run.sh <input_dir> <mask_dir> <output_dir>
```

Default modes are:

```text
dark white mean median mode random gray blur
```

Override modes with:

```bash
BG_TRANSFORM_MODES="white blur gray" bash apps/background_transformation/run.sh
```
