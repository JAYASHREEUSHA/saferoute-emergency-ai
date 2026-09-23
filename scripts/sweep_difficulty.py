"""Step 6: does the result hold as the emergency gets harder (faster fire, later warning)?
Run:  python scripts/sweep_difficulty.py --n 150
"""
import argparse, sys
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from saferoute.buildings import grid_building
from saferoute.scenario import ScenarioParams
from saferoute.sensitivity import difficulty_sweep, render_difficulty_sweep

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=60, help="oracle search cost rises sharply in the harder settings, so this defaults lower than the other sweeps")
ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()

base = ScenarioParams()
settings = {
    "easy (base)":       base,
    "faster fire":       replace(base, v_fire_range=(0.2, 0.6)),
    "later warning":     replace(base, t_ignite_range=(-120.0, -60.0)),  # fire already spreading 60-120s before evac starts
    "faster+later warn": replace(base, v_fire_range=(0.2, 0.6), t_ignite_range=(-120.0, -60.0)),
}
g = grid_building(rows=6, cols=10, spacing=12.0, exits={(0,0),(0,9),(5,0),(5,9),(0,5),(5,4)})
rows = difficulty_sweep(g, settings, a.n, a.seed)
text = f"# Difficulty sweep ({a.n} scenarios per setting)\n\n" + render_difficulty_sweep(rows) + (
    "\n\nOracle success % dropping toward 0 means most scenarios are unwinnable by ANY policy at "
    "that difficulty — a shrinking dose gap there reflects a harder benchmark, not a worse method. "
    "Read the dose gap alongside the oracle rate, not in isolation.\n"
)
out = ROOT / "results"; out.mkdir(exist_ok=True)
(out / "sweep_difficulty.md").write_text(text)
print(text)
