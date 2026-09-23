"""Step 6: turn one mechanism off at a time (hysteresis, crowd term, perception noise).
Run:  python scripts/run_ablations.py --n 150
"""
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from saferoute.buildings import grid_building
from saferoute.sensitivity import ablation_runs, render_ablations

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=150)
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

g = grid_building(rows=6, cols=10, spacing=12.0, exits={(0,0),(0,9),(5,0),(5,9),(0,5),(5,4)})
rows = ablation_runs(g, a.n, a.seed)
text = f"# Ablations ({a.n} scenarios, all vs shortest_path baseline)\n\n" + render_ablations(rows) + (
    "\n\nno_hysteresis reroutes the instant a cheaper option appears (no switch margin) — compare "
    "its mean reroutes to the full method's. no_crowd_term disables crowd-based slowdown/cost. "
    "perfect_perception uses ground-truth hazards with no latency (upper bound on this policy).\n"
)
out = ROOT / "results"; out.mkdir(exist_ok=True)
(out / "ablations.md").write_text(text)
print(text)
