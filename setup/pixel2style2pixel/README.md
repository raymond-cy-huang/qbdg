# pixel2style2pixel Setup

The QDBG pSp app expects a conda environment named `pixel2style2pixel` by
default. Recreate it from the exported environment file:

```bash
conda env create -f setup/pixel2style2pixel/environment.yml
conda activate pixel2style2pixel
```

Files:

- `environment.yml`: full exported environment used by the QDBG pSp app.
- `environment.from-history.yml`: conda history export retained for inspection.
- `upstream_psp_env.yaml`: original upstream pSp environment file from
  `subprojects/pixel2style2pixel/environment/psp_env.yaml`.

The upstream pSp file is Python 3.6 / torch 1.6-era and is kept as reference only.
