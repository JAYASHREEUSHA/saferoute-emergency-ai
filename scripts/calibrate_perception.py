"""Measure real fire/smoke detector precision, recall and per-frame latency against a
held-out labeled test set, and print PerceptionConfig values to use in scripts/run_experiment.py.

Do NOT skip this: Step 2's evaluation used ASSUMED noise (recall=0.9, fp=0.01, latency=2s).
Re-running the experiment with numbers from this script turns those into honest results.

Usage:
  python scripts/calibrate_perception.py --labels eval/labels.csv --weights runs/fire_smoke/weights/best.pt
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saferoute.vision import YoloFireSmokeDetector  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--labels", default=str(ROOT / "eval" / "labels.csv"))
ap.add_argument("--weights", default=str(ROOT / "runs" / "fire_smoke" / "weights" / "best.pt"))
ap.add_argument("--conf", type=float, default=0.25, help="confidence threshold to evaluate at")
a = ap.parse_args()

if not Path(a.weights).exists():
    raise SystemExit(f"No weights at {a.weights}. Run training/train_fire_smoke.py or the Colab notebook first.")

import cv2  # noqa: E402

rows = list(csv.DictReader(open(a.labels)))
if not rows:
    raise SystemExit(f"No rows in {a.labels}. See eval/README.md for the expected format.")

detector = YoloFireSmokeDetector(a.weights, conf=a.conf)
truth: dict[tuple[str, str], int] = {(r["frame"], r["cls"]): int(r["present"]) for r in rows}
frames = sorted({r["frame"] for r in rows})

counts = {c: {"tp": 0, "fn": 0, "fp": 0, "tn": 0} for c in ("fire", "smoke")}
latencies = []

for frame_path in frames:
    img = cv2.imread(str(ROOT / frame_path)) if not Path(frame_path).is_absolute() else cv2.imread(frame_path)
    if img is None:
        print(f"[skip] could not read {frame_path}")
        continue
    t0 = time.perf_counter()
    det = detector.detect(img)
    latencies.append((time.perf_counter() - t0) * 1000.0)
    for c in ("fire", "smoke"):
        predicted = det.max_conf(c) >= a.conf
        actual = bool(truth.get((frame_path, c), 0))
        key = ("tp" if actual else "fp") if predicted else ("fn" if actual else "tn")
        counts[c][key] += 1

print(f"Evaluated {len(frames)} frames at conf={a.conf}\n")
print(f"{'Class':6} {'Precision':>10} {'Recall':>8} {'FP rate':>8} {'TP':>5} {'FN':>5} {'FP':>5} {'TN':>5}")
suggested = {}
for c, k in counts.items():
    tp, fn, fp, tn = k["tp"], k["fn"], k["fp"], k["tn"]
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    fp_rate = fp / (fp + tn) if (fp + tn) else float("nan")
    print(f"{c:6} {precision:10.3f} {recall:8.3f} {fp_rate:8.3f} {tp:5} {fn:5} {fp:5} {tn:5}")
    suggested[c] = (recall, fp_rate)

mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
print(f"\nMean inference latency: {mean_latency:.1f} ms/frame")

recall = min(v[0] for v in suggested.values() if v[0] == v[0])  # nan-safe min
fp_rate = max(v[1] for v in suggested.values() if v[1] == v[1])
print("\nSuggested PerceptionConfig (conservative: worst of fire/smoke) for scripts/run_experiment.py:")
print(f"  --recall {recall:.2f} --fp {fp_rate:.3f} --latency {max(2.0, mean_latency / 1000.0 + 1.0):.1f}")
print("  (latency = measured inference time + an assumed ~1s pipeline/network delay; adjust once measured end-to-end)")
