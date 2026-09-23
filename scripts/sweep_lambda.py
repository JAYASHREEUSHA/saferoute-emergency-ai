"""Step 6: how the hazard penalty lambda trades off evacuation time against exposure.
Run:  python scripts/sweep_lambda.py --n 150
"""
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from saferoute.buildings import grid_building
from saferoute.sensitivity import lambda_sweep, render_lambda_sweep

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=150)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--lambdas", type=float, nargs="+", default=[0, 15, 30, 60, 120, 250])
a = ap.parse_args()

g = grid_building(rows=6, cols=10, spacing=12.0, exits={(0,0),(0,9),(5,0),(5,9),(0,5),(5,4)})
rows = lambda_sweep(g, a.lambdas, a.n, a.seed)
text = f"# Lambda sweep ({a.n} scenarios per value)\n\n" + render_lambda_sweep(rows) + (
    "\n\nNote: at lambda=0 the hazard PENALTY is zero, but dynamic_risk still (a) treats a hazard "
    "above the fire/block threshold as a hard constraint regardless of lambda, and (b) is crowd-aware "
    "(shortest_path is blind to both). So lambda=0 is NOT expected to match shortest_path exactly - "
    "the remaining gap at lambda=0 is what those two mechanisms alone contribute. Pick the smallest "
    "lambda where the ADDITIONAL gap beyond lambda=0 plateaus, then check mean time hasn't grown much.\n"
)
out = ROOT / "results"; out.mkdir(exist_ok=True)
(out / "sweep_lambda.md").write_text(text)
print(text)
