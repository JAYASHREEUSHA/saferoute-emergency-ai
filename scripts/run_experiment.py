"""Monte Carlo comparison of routing policies in simulation.

Examples:
  python scripts/run_experiment.py --plan grid --n 300
  python scripts/run_experiment.py --plan mall --n 300 --perception perfect
  python scripts/run_experiment.py --plan grid --n 300 --lam 30
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saferoute import BuildingGraph, RiskConfig  # noqa: E402
from saferoute.buildings import grid_building  # noqa: E402
from saferoute.experiment import default_specs, run_experiment, summarize  # noqa: E402
from saferoute.perception import PerceptionConfig  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--plan", choices=["mall", "grid"], default="grid")
ap.add_argument("--n", type=int, default=300, help="number of random scenarios")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--lam", type=float, default=RiskConfig().lam, help="hazard penalty (seconds-equivalent)")
ap.add_argument("--perception", choices=["noisy", "perfect"], default="noisy")
ap.add_argument("--recall", type=float, default=PerceptionConfig().recall)
ap.add_argument("--fp", type=float, default=PerceptionConfig().fp_rate)
ap.add_argument("--latency", type=float, default=PerceptionConfig().latency_s)
ap.add_argument("--perception-config", default=None, help="JSON from scripts/evaluate_detector.py (overrides recall/fp/latency)")
ap.add_argument("--out", default="results")
a = ap.parse_args()

if a.plan == "mall":
    graph = BuildingGraph.from_json(ROOT / "data" / "floorplan_mall.json")
else:  # 6 x 10 corridor grid, 12 m spacing, six exits (four corners + one mid-point on each long side)
    graph = grid_building(rows=6, cols=10, spacing=12.0,
                          exits={(0, 0), (0, 9), (5, 0), (5, 9), (0, 5), (5, 4)})
risk = RiskConfig(lam=a.lam)
if a.perception_config:
    from dataclasses import replace
    pcfg = replace(PerceptionConfig.from_json(a.perception_config), mode=a.perception)
else:
    pcfg = PerceptionConfig(mode=a.perception, recall=a.recall, fp_rate=a.fp, latency_s=a.latency)

rows = run_experiment(graph, a.n, a.seed, default_specs(risk, pcfg), wcfg=RiskConfig())

out = Path(a.out)
out.mkdir(exist_ok=True)
tag = f"{a.plan}_n{a.n}_seed{a.seed}_lam{a.lam:g}_{a.perception}" + ("_measured" if a.perception_config else "")
with open(out / f"runs_{tag}.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

text = (
    f"# {graph.name} | lambda={a.lam:g} | perception={a.perception} "
    f"(recall={pcfg.recall}, fp={pcfg.fp_rate}, latency={pcfg.latency_s}s"
    f"{', measured: ' + a.perception_config if a.perception_config else ''})\n\n" + summarize(rows)
)
(out / f"summary_{tag}.md").write_text(text + "\n")
print(text)
print(f"\nSaved: {out / f'runs_{tag}.csv'}  and  {out / f'summary_{tag}.md'}")
