# Fine-tuning the fire/smoke detector

Training YOLOv8n on a CPU laptop is impractically slow (hours per epoch). Use a free GPU
notebook (Colab or Kaggle) instead: `notebooks/train_fire_smoke_colab.ipynb`.

## 1. Get a dataset

**D-Fire** (recommended: YOLO-format labels already, ~21k images, permissive research use —
check the license on the dataset page before any commercial use):
search "D-Fire dataset GitHub" (gaiasd/DFireDataset) or use a mirror on Roboflow Universe
("D-Fire" or "fire smoke detection"). Roboflow lets you export directly in YOLOv8 format,
which is the easiest path if you don't want to convert annotations yourself.

Expected layout after download (matches `training/dfire.yaml`):
```
datasets/dfire/
  images/train/*.jpg   labels/train/*.txt
  images/val/*.jpg     labels/val/*.txt
```
Each label file is YOLO format: `class x_center y_center width height` (normalized 0-1),
class 0 = fire, class 1 = smoke (relabel if your source uses a different order).

## 2. Train (on a GPU)

Colab: upload `training/` and `notebooks/train_fire_smoke_colab.ipynb`, mount/download the
dataset into `datasets/dfire/`, run all cells. It fine-tunes `yolov8n.pt` and downloads
`best.pt` at the end.

Local GPU:
```bash
pip install ultralytics
python training/train_fire_smoke.py --data training/dfire.yaml --epochs 60
```

## 3. Use the trained weights

Copy the resulting `best.pt` to `runs/fire_smoke/weights/best.pt` (the default path in
`data/camera_config.json`), or edit that path in the config.

## 4. Measure real detector performance (do not skip this)

The simulator in Step 2 used ASSUMED detector noise (recall=0.9, fp=0.01, latency=2s).
Run `scripts/calibrate_perception.py` against a held-out labeled test set to replace those
assumptions with measured numbers, then re-run `scripts/run_experiment.py` with `--recall`
`--fp` `--latency` set to what you measured, to get honest evaluation numbers.
