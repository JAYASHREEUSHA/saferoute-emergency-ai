"""Scripted demo: fire near Exit A, crowd at Exit B, smoke near Exit C -> dynamic re-routing.

Hazards are mocked here; in Step 3 they come from the vision module.
Run:  python scripts/run_scenario.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saferoute import BuildingGraph, EdgeObservation, RiskConfig, RoutePlanner, explain  # noqa: E402

graph = BuildingGraph.from_json(ROOT / "data" / "floorplan_mall.json")
cfg = RiskConfig()
planner = RoutePlanner(graph, cfg)

obs: dict[str, EdgeObservation] = {}

# (title, changes to observations, user position after the change)
timeline = [
    ("T0  All clear, user at Start", {}, "S"),
    ("T1  Fire detected on Corridor A", {"S-JA": EdgeObservation(p_fire=0.90)}, "S"),
    (
        "T2  Crowd builds up in Corridor B",
        {"S-JB": EdgeObservation(people=30), "JB-EXIT_B": EdgeObservation(people=150)},
        "S",
    ),
    ("T3  User walks to Junction C1", {}, "C1"),
    ("T4  Smoke detected on Corridor C (middle)", {"C1-C2": EdgeObservation(p_smoke=0.85)}, "C1"),
]


def fmt(v):
    return "-" if v is None else v


for title, changes, user_at in timeline:
    obs.update(changes)
    decision = planner.update(obs, user_at)
    ex = explain(decision, graph, obs, cfg)

    print("=" * 78)
    print(f"{title}   [user at: {graph.label(user_at)}]")
    print("-" * 78)
    print(ex.headline)
    if ex.voice != ex.headline:
        print(f"Voice: {ex.voice}")
    print()
    print(f"{'Exit':8} {'Status':9} {'Dist(m)':>8} {'Time(s)':>8} {'Risk':>6} {'Cost':>7}")
    for row in ex.table:
        star = "*" if row["recommended"] else " "
        print(
            f"{row['exit']:8} {row['status']:9} {fmt(row['distance_m']):>8} {fmt(row['travel_time_s']):>8} "
            f"{fmt(row['route_risk']):>6} {fmt(row['cost']):>7} {star}"
        )
    print()
    for r in ex.reasons:
        print(f"  - {r}")
print("=" * 78)
