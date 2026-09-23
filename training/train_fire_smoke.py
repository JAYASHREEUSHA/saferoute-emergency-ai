"""Fine-tune YOLOv8n on D-Fire (fire/smoke). Meant to run on a GPU (Colab/Kaggle) — see
notebooks/train_fire_smoke_colab.ipynb for a ready-to-run version, or run this directly if
you have a local GPU. Do NOT train this on a CPU-only laptop; it will take hours per epoch.

Usage:
  python training/train_fire_smoke.py --data training/dfire.yaml --epochs 60
"""
import argparse

from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="training/dfire.yaml")
ap.add_argument("--model", default="yolov8n.pt", help="pretrained checkpoint to fine-tune from")
ap.add_argument("--epochs", type=int, default=60)
ap.add_argument("--imgsz", type=int, default=640)
ap.add_argument("--batch", type=int, default=16)
ap.add_argument("--project", default="runs")
ap.add_argument("--name", default="fire_smoke")
a = ap.parse_args()

model = YOLO(a.model)
model.train(
    data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch,
    project=a.project, name=a.name,
    patience=15,          # early stop if val metrics plateau
    val=True,
    plots=True,
)
metrics = model.val()  # final val metrics: precision, recall, mAP50, mAP50-95 per class
print(metrics.box.maps)  # mAP50-95 per class
print(f"\nBest weights: {a.project}/{a.name}/weights/best.pt")
print("Copy or point runs/fire_smoke/weights/best.pt (or --config in run_camera_demo.py) at this file.")
