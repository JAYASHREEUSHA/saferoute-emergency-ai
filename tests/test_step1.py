import math
import random
from pathlib import Path

import pytest

from saferoute import BuildingGraph, EdgeObservation, RiskConfig, RoutePlanner, explain
from saferoute.graph import Edge, Node
from saferoute.planner import astar
from saferoute.risk import edge_cost, walking_speed

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def graph():
    return BuildingGraph.from_json(ROOT / "data" / "floorplan_mall.json")


@pytest.fixture()
def cfg():
    return RiskConfig()


# ---------------------------------------------------------------- graph
def test_floorplan_loads(graph):
    assert set(graph.exits) == {"EXIT_A", "EXIT_B", "EXIT_C"}
    assert graph.edges["S-JA"].length == pytest.approx(8.0)


def test_edge_shorter_than_straight_line_rejected():
    nodes = [Node("a", 0, 0), Node("b", 10, 0, kind="exit")]
    with pytest.raises(ValueError):
        BuildingGraph("bad", nodes, [Edge("e", "a", "b", length=5.0)])


def test_unknown_node_rejected():
    nodes = [Node("a", 0, 0, kind="exit")]
    with pytest.raises(ValueError):
        BuildingGraph("bad", nodes, [Edge("e", "a", "zzz", length=5.0)])


# ---------------------------------------------------------------- risk model
def test_walking_speed_monotonic_and_bounded(cfg):
    speeds = [walking_speed(r / 10, cfg) for r in range(0, 70)]
    assert all(a >= b - 1e-12 for a, b in zip(speeds, speeds[1:]))
    assert max(speeds) <= cfg.v_free + 1e-12
    assert speeds[0] == pytest.approx(cfg.v_free)
    assert walking_speed(cfg.rho_max, cfg) == cfg.v_min
    assert walking_speed(0.05, cfg) == pytest.approx(cfg.v_free, rel=1e-3)


def test_edge_cost_never_below_free_flow(graph, cfg):
    """Admissibility of the A* heuristic depends on this."""
    rng = random.Random(1)
    for e in graph.edges.values():
        for _ in range(100):
            obs = EdgeObservation(rng.random(), rng.random(), rng.random(), rng.uniform(0, 200))
            c = edge_cost(e, obs, cfg, relax=True)
            assert c.total >= e.length / cfg.v_free - 1e-9


def test_crowd_adds_delay(graph, cfg):
    e = graph.edges["JB-EXIT_B"]
    empty = edge_cost(e, EdgeObservation(), cfg)
    crowded = edge_cost(e, EdgeObservation(people=150), cfg)
    assert empty.crowd_delay == pytest.approx(0.0, abs=1e-6)
    assert crowded.crowd_delay > 20
    assert crowded.density == pytest.approx(2.5)


def test_fire_above_threshold_blocks(graph, cfg):
    e = graph.edges["S-JA"]
    assert edge_cost(e, EdgeObservation(p_fire=0.9), cfg).blocked
    assert not edge_cost(e, EdgeObservation(p_fire=0.3), cfg).blocked
    assert not edge_cost(e, EdgeObservation(p_smoke=1.0), cfg).blocked  # smoke is a penalty, not a wall


def test_unmonitored_edge_uses_prior(graph, cfg):
    c = edge_cost(graph.edges["C1-JB"], None, cfg)
    assert c.risk == pytest.approx(cfg.unknown_prior_risk)
    assert edge_cost(graph.edges["S-JA"], None, cfg).risk == 0.0  # covered by a camera, nothing seen


# ---------------------------------------------------------------- A*
def test_astar_matches_dijkstra_on_random_observations(graph, cfg):
    rng = random.Random(7)
    for _ in range(300):
        obs = {}
        for eid in graph.edges:
            if rng.random() < 0.6:
                obs[eid] = EdgeObservation(
                    p_fire=rng.choice([0, 0, 0.2, 0.9]),
                    p_smoke=rng.random() * rng.choice([0, 1]),
                    people=rng.uniform(0, 120),
                )
        costs = {eid: edge_cost(e, obs.get(eid), cfg) for eid, e in graph.edges.items()}

        def cost_fn(e):
            c = costs[e.id]
            return math.inf if c.blocked else c.total

        start = rng.choice(list(graph.nodes))
        for ex in graph.exits:
            a = astar(graph, start, ex, cost_fn, lambda n, ex=ex: graph.euclid(n, ex) / cfg.v_free)
            d = astar(graph, start, ex, cost_fn, None)
            assert (a is None) == (d is None)
            if a is not None:
                assert a[2] == pytest.approx(d[2])


# ---------------------------------------------------------------- planner scenario
def _run(graph, cfg):
    planner = RoutePlanner(graph, cfg)
    obs = {}
    out = []
    steps = [
        ({}, "S"),
        ({"S-JA": EdgeObservation(p_fire=0.9)}, "S"),
        ({"S-JB": EdgeObservation(people=30), "JB-EXIT_B": EdgeObservation(people=150)}, "S"),
        ({}, "C1"),
        ({"C1-C2": EdgeObservation(p_smoke=0.85)}, "C1"),
    ]
    for changes, at in steps:
        obs.update(changes)
        d = planner.update(obs, at)
        out.append((d, explain(d, graph, obs, cfg)))
    return out


def test_demo_scenario_sequence(graph, cfg):
    (d0, _), (d1, e1), (d2, e2), (d3, _), (d4, e4) = _run(graph, cfg)
    assert (d0.event, d0.recommended.exit_id) == ("initial", "EXIT_A")  # shortest exit first
    assert (d1.event, d1.recommended.exit_id) == ("reroute_blocked", "EXIT_B")  # fire on A
    assert (d2.event, d2.recommended.exit_id) == ("reroute_better", "EXIT_C")  # crowd on B
    assert (d3.event, d3.recommended.exit_id) == ("keep", "EXIT_C")
    assert (d4.event, d4.recommended.exit_id) == ("reroute_better", "EXIT_B")  # smoke on C

    assert "fire" in e1.headline and "Exit A" in e1.headline
    assert any(r.startswith("Exit A rejected: fire") for r in e1.reasons)
    assert "crowding" in e2.headline
    assert "smoke" in e4.headline and "Recalculating" in e4.headline


def test_risk_aware_choice_is_longer_than_shortest(graph, cfg):
    (_, _), (_, _), (d2, _), _, _ = _run(graph, cfg)
    assert d2.recommended.length_m > 20.0  # Exit A is 20 m; the chosen exit is farther but cheaper


def test_hysteresis_prevents_flip_flop(graph, cfg):
    planner = RoutePlanner(graph, cfg)
    assert planner.update({}, "S").recommended.exit_id == "EXIT_A"
    # Mild smoke: A's cost rises by 6 s, tying with B. Margin is 5 s, so we stay.
    d = planner.update({"S-JA": EdgeObservation(p_smoke=0.1)}, "S")
    assert d.event == "keep" and d.recommended.exit_id == "EXIT_A"
    # Clear smoke: A now costs clearly more than B, so we switch.
    d = planner.update({"S-JA": EdgeObservation(p_smoke=0.5)}, "S")
    assert d.event == "reroute_better" and d.recommended.exit_id == "EXIT_B"


def test_no_safe_route_fallback(graph, cfg):
    planner = RoutePlanner(graph, cfg)
    obs = {eid: EdgeObservation(p_fire=0.9) for eid in ("S-JA", "S-JB", "S-C1")}
    d = planner.update(obs, "S")
    assert d.no_safe_route and d.event == "no_safe_route"
    assert d.recommended is not None and not d.recommended.feasible
    ex = explain(d, graph, obs, cfg)
    assert "no safe route" in ex.headline.lower()
    assert "official alarms" in ex.headline


def test_arrival(graph, cfg):
    planner = RoutePlanner(graph, cfg)
    d = planner.update({}, "EXIT_A")
    assert d.event == "arrived" and d.recommended is None


def test_route_risk_combines_edges(graph, cfg):
    # Exit A can only be reached via S-JA -> JA-EXIT_A, so the route cannot detour around the smoke.
    obs = {"S-JA": EdgeObservation(p_smoke=0.5), "JA-EXIT_A": EdgeObservation(p_smoke=0.5)}
    from saferoute.planner import evaluate_exits

    opt = next(o for o in evaluate_exits(graph, obs, "S", cfg) if o.exit_id == "EXIT_A")
    assert opt.route_risk == pytest.approx(1 - 0.5 * 0.5)


def test_planner_detours_around_smoke_via_unmonitored_link(graph, cfg):
    """Exit B via the cross link (prior risk 0.05) beats the direct corridor with heavy smoke."""
    from saferoute.planner import evaluate_exits

    obs = {"S-JB": EdgeObservation(p_smoke=0.5)}
    opt = next(o for o in evaluate_exits(graph, obs, "S", cfg) if o.exit_id == "EXIT_B")
    assert "C1-JB" in opt.edge_ids and "S-JB" not in opt.edge_ids
