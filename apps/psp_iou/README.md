# pSp Background IoU App

This app visualizes and measures the background-mask overlap between a GT image
and a pSp frontalization result.

Mask convention:

- white: foreground/person
- black: background

The reported IoU is therefore the IoU of the black/background region.

## Run

```bash
bash apps/psp_iou/run.sh
```

Default inputs:

```text
apps/psp_iou/inputs/gt.jpg
apps/psp_iou/inputs/gt_mask.png
apps/psp_iou/inputs/psp_front.jpg
apps/psp_iou/inputs/psp_front_mask.jpg
```

Outputs:

- `metrics.csv`
- `00_summary_2x2_background_iou.png`
- per-image overlay/border visualizations
