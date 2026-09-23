"""Step 6: how much of dynamic_risk's advantage survives as the detector gets worse.
Run:  python scripts/sweep_perception.py --n 150
"""
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from saferoute.buildings import grid_building
from saferoute.perception import PerceptionConfig
from saferoute.sensitivity import perception_sweep, render_perception_sweep

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=150)
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

configs = {
    "perfect":       PerceptionConfig(mode="perfect", latency_s=0.0),
    "good (default)": PerceptionConfig(recall=0.90, fp_rate=0.01, latency_s=2.0),
    "moderate":      PerceptionConfig(recall=0.75, fp_rate=0.03, latency_s=4.0),
    "poor":          PerceptionConfig(recall=0.55, fp_rate=0.08, latency_s=6.0),
    "very poor":     PerceptionConfig(recall=0.35, fp_rate=0.15, latency_s=8.0),
}
g = grid_building(rows=6, cols=10, spacing=12.0, exits={(0,0),(0,9),(5,0),(5,9),(0,5),(5,4)})
rows = perception_sweep(g, configs, a.n, a.seed)
text = f"# Detector-noise sweep ({a.n} scenarios per setting)\n\n" + render_perception_sweep(rows) + (
    "\n\n'good (default)' matches the noise levels assumed in Step 2's headline results. "
    "'perfect' is the ceiling (routing logic alone, no perception error). Replace 'good (default)' "
    "with numbers from scripts/calibrate_perception.py once the fire/smoke model is trained.\n"
)
out = ROOT / "results"; out.mkdir(exist_ok=True)
(out / "sweep_perception.md").write_text(text)
print(text)
