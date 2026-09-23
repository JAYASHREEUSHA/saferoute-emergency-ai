import random
from pathlib import Path

import pytest

from saferoute import BuildingGraph, RiskConfig
from saferoute.buildings import grid_building
from saferoute.experiment import default_specs, run_experiment, run_scenario, summarize
from saferoute.oracle import oracle_outcome
from saferoute.perception import Perception, PerceptionConfig
from saferoute.policies import DynamicRiskPolicy, ShortestPathPolicy, StaticRiskPolicy
from saferoute.scenario import Scenario, generate_scenario
from saferoute.sim import SimConfig, simulate, traverse

ROOT = Path(__file__).resolve().parents[1]
PERFECT = PerceptionConfig(mode="perfect", latency_s=0.0)


@pytest.fixture()
def mall():
    return BuildingGraph.from_json(ROOT / "data" / "floorplan_mall.json")


@pytest.fixture()
def small_grid():
    return grid_building(rows=4, cols=5, spacing=10.0, exits={(0, 0), (3, 4), (0, 4)})


def _run(graph, scn, policy, pcfg=PERFECT, scfg=None, seed=0):
    perc = Perception(graph, scn, pcfg, random.Random(seed))
    return simulate(graph, scn, policy, perc, scfg or SimConfig(), RiskConfig())


# ------------------------------------------------------------------ world model
def test_hazards_are_monotone_in_time(small_grid):
    for seed in range(20):
        scn = generate_scenario(small_grid, random.Random(seed))
        for eid in small_grid.edges:
            prev = (False, 0.0, False, 0.0)
            for t in range(-100, 400, 7):
                cur = (scn.fire_on(eid, t), scn.smoke_level(eid, t), scn.blocked(eid, t), scn.people(eid, t))
                assert all(c >= p - 1e-9 for c, p in zip(cur, prev))
                prev = cur


def test_traverse_without_hazards(mall):
    scn = Scenario(mall, "S")
    r = traverse(scn, mall.edges["S-JA"], 0.0, 0.0, SimConfig(), RiskConfig())
    assert r.t_end == pytest.approx(8.0 / 1.34, rel=1e-6)
    assert r.fed_end == 0.0 and not r.incapacitated


def test_smoke_adds_dose_and_slows(mall):
    clear = traverse(Scenario(mall, "S"), mall.edges["S-JA"], 0.0, 0.0, SimConfig(), RiskConfig())
    smoky = Scenario(mall, "S", smoke_time={"S-JA": -100.0}, smoke_ramp_s=1.0, smoke_max=1.0)
    r = traverse(smoky, mall.edges["S-JA"], 0.0, 0.0, SimConfig(), RiskConfig())
    assert r.fed_end > 0 and r.t_end > clear.t_end


def test_fire_contact_is_dangerous(mall):
    scn = Scenario(mall, "S", fire_time={"JA-EXIT_A": -5.0})
    r = traverse(scn, mall.edges["JA-EXIT_A"], 0.0, 0.0, SimConfig(), RiskConfig())
    assert r.fed_end > 0.5  # ~9 s in flames at 1/10 per second


# ------------------------------------------------------------------ policies
def test_hazard_free_all_policies_reach_nearest_exit(mall):
    scn = Scenario(mall, "S")
    for pol in (ShortestPathPolicy(), StaticRiskPolicy(RiskConfig()), DynamicRiskPolicy(RiskConfig())):
        o = _run(mall, scn, pol)
        assert o.success and o.fed == 0.0
        assert o.path[-1] == "EXIT_A" and o.evac_time == pytest.approx(20.0 / 1.34, rel=1e-6)


def test_visible_fire_is_never_entered(mall):
    scn = Scenario(mall, "S", fire_time={"S-JA": -10.0})
    o = _run(mall, scn, ShortestPathPolicy())
    assert o.success and "JA" not in o.path and o.fed == 0.0


def test_dynamic_avoids_smoke_that_shortest_path_walks_into(mall):
    scn = Scenario(mall, "S", smoke_time={"S-JA": -200.0, "JA-EXIT_A": -200.0}, smoke_ramp_s=1.0, smoke_max=1.0)
    sp = _run(mall, scn, ShortestPathPolicy())
    dyn = _run(mall, scn, DynamicRiskPolicy(RiskConfig()))
    assert sp.success and dyn.success
    assert sp.fed > 0.3 and dyn.fed == 0.0
    assert dyn.path[-1] != "EXIT_A"


def test_terminates_when_every_route_is_blocked(mall):
    """Regression: a fallback plan through a known-blocked corridor must not loop forever."""
    scn = Scenario(mall, "S", fire_time={"S-JA": -10.0, "S-JB": -10.0, "S-C1": -10.0})
    scfg = SimConfig(t_max=20.0)
    for pol in (ShortestPathPolicy(), StaticRiskPolicy(RiskConfig()), DynamicRiskPolicy(RiskConfig())):
        o = _run(mall, scn, pol, scfg=scfg)
        assert not o.success and o.timed_out


# ------------------------------------------------------------------ oracle and pairing
@pytest.mark.parametrize("plan", ["mall", "grid"])
def test_oracle_is_a_lower_bound(plan, mall, small_grid):
    graph = mall if plan == "mall" else small_grid
    scfg, wcfg = SimConfig(), RiskConfig()
    specs = default_specs(RiskConfig(), PerceptionConfig())
    for seed in range(25):
        scn = generate_scenario(graph, random.Random(seed))
        outs = run_scenario(graph, scn, specs, seed, scfg, wcfg)
        orc = outs["oracle"]
        for name, o in outs.items():
            if name != "oracle" and o.success:
                assert orc.success, f"{name} escaped but oracle did not (seed {seed})"
                assert orc.fed <= o.fed + 1e-9, f"{name} beat the oracle on dose (seed {seed})"


def test_same_seed_gives_identical_detector_noise(small_grid):
    scn = generate_scenario(small_grid, random.Random(3))
    a = Perception(small_grid, scn, PerceptionConfig(), random.Random(11))
    b = Perception(small_grid, scn, PerceptionConfig(), random.Random(11))
    for t in (0, 5, 17):
        a.advance_to(t)
        b.advance_to(t)
        assert a.observations() == b.observations()


def test_experiment_is_reproducible(mall):
    specs = default_specs(RiskConfig(), PerceptionConfig())
    r1 = run_experiment(mall, 8, 5, specs)
    r2 = run_experiment(mall, 8, 5, specs)
    keys = ("scenario", "policy", "success", "evac_time", "fed", "smoke_time", "fire_time", "path_length")
    assert [[r[k] for k in keys] for r in r1] == [[r[k] for k in keys] for r in r2]


def test_summary_renders(mall):
    rows = run_experiment(mall, 12, 1, default_specs(RiskConfig(), PerceptionConfig()))
    text = summarize(rows)
    for name in ("shortest_path", "static_risk", "dynamic_risk", "oracle"):
        assert name in text
