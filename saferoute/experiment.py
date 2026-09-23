"""Run all policies on the same scenarios (paired design) and summarise with bootstrap CIs."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace
from typing import Callable

from .graph import BuildingGraph
from .oracle import oracle_outcome
from .perception import Perception, PerceptionConfig
from .policies import DynamicRiskPolicy, Policy, ShortestPathPolicy, StaticRiskPolicy
from .risk import RiskConfig
from .scenario import Scenario, ScenarioParams, generate_scenario
from .sim import Outcome, SimConfig, simulate


@dataclass
class PolicySpec:
    name: str
    factory: Callable[[], Policy]
    perception: PerceptionConfig


def default_specs(risk_cfg: RiskConfig, pcfg: PerceptionConfig) -> list[PolicySpec]:
    perfect = replace(pcfg, mode="perfect", latency_s=0.0)  # no noise AND no latency: upper bound for perception
    return [
        PolicySpec("shortest_path", lambda: ShortestPathPolicy(), pcfg),
        PolicySpec("static_risk", lambda: StaticRiskPolicy(risk_cfg), pcfg),
        PolicySpec("dynamic_risk", lambda: DynamicRiskPolicy(risk_cfg), pcfg),
        PolicySpec("dynamic_perfect_perception", lambda: DynamicRiskPolicy(risk_cfg, "dynamic_perfect_perception"), perfect),
    ]


def run_scenario(
    graph: BuildingGraph, scn: Scenario, specs: list[PolicySpec], seed: int,
    scfg: SimConfig, wcfg: RiskConfig, include_oracle: bool = True,
) -> dict[str, Outcome]:
    outs: dict[str, Outcome] = {}
    for spec in specs:
        perc = Perception(graph, scn, spec.perception, random.Random(seed))  # same noise stream for every policy
        outs[spec.name] = simulate(graph, scn, spec.factory(), perc, scfg, wcfg)
    if include_oracle:
        outs["oracle"] = oracle_outcome(graph, scn, scfg, wcfg)
    return outs


def run_experiment(
    graph: BuildingGraph, n: int, seed: int, specs: list[PolicySpec],
    params: ScenarioParams | None = None, scfg: SimConfig | None = None, wcfg: RiskConfig | None = None,
) -> list[dict]:
    scfg, wcfg = scfg or SimConfig(), wcfg or RiskConfig()
    rows = []
    for i in range(n):
        s = seed * 1_000_003 + i
        scn = generate_scenario(graph, random.Random(s), params)
        for name, o in run_scenario(graph, scn, specs, s, scfg, wcfg).items():
            rows.append(
                dict(
                    scenario=i, policy=name, start=scn.start, success=int(o.success),
                    evac_time=o.evac_time if o.evac_time is not None else "", fed=round(o.fed, 4),
                    incapacitated=int(o.incapacitated), timed_out=int(o.timed_out),
                    smoke_time=round(o.smoke_time, 2), fire_time=round(o.fire_time, 2),
                    wait_time=round(o.wait_time, 2), path_length=round(o.path_length, 1),
                    n_reroutes=o.n_reroutes, plan_ms=round(o.plan_ms, 3), n_plans=o.n_plans,
                )
            )
    return rows


# ------------------------------------------------------------------ statistics (stdlib only)
def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def bootstrap_ci(values, B: int = 2000, seed: int = 0, alpha: float = 0.05):
    """Percentile bootstrap CI for the mean."""
    vals = list(values)
    if not vals:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(vals)
    means = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return means[int(B * alpha / 2)], means[int(B * (1 - alpha / 2)) - 1]


def by_policy(rows: list[dict]) -> dict[str, dict[int, dict]]:
    out: dict[str, dict[int, dict]] = {}
    for r in rows:
        out.setdefault(r["policy"], {})[r["scenario"]] = r
    return out


STRESS_DOSE = 0.05  # a scenario is "hazard-relevant" if the hazard-blind shortest route gets a dose >= this


def _table(pol: dict, order: list[str], ids: list[int]) -> list[str]:
    L = ["| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |",
         "|---|---|---|---|---|---|---|---|"]
    for p in order:
        rs = [pol[p][i] for i in ids]
        succ, fed = [r["success"] for r in rs], [r["fed"] for r in rs]
        ts = [r["evac_time"] for r in rs if r["success"]]
        slo, shi = bootstrap_ci(succ)
        flo, fhi = bootstrap_ci(fed)
        L.append(
            f"| {p} | {100*mean(succ):.1f} [{100*slo:.1f}, {100*shi:.1f}] | {mean(fed):.3f} [{flo:.3f}, {fhi:.3f}] "
            f"| {mean(ts):.1f} / {percentile(ts, .95):.1f} | {mean(r['smoke_time'] for r in rs):.1f} "
            f"| {mean(r['fire_time'] for r in rs):.1f} | {mean(r['n_reroutes'] for r in rs):.2f} "
            f"| {mean(r['plan_ms']/max(1,r['n_plans']) for r in rs):.3f} |"
        )
    return L


def _paired(pol: dict, order: list[str], ids: list[int], base: str) -> list[str]:
    L = [f"Paired differences vs `{base}` (negative dose / positive success = better):", "",
         "| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |", "|---|---|---|---|"]
    for p in order:
        if p == base:
            continue
        ds = [100 * (pol[p][i]["success"] - pol[base][i]["success"]) for i in ids]
        df = [pol[p][i]["fed"] - pol[base][i]["fed"] for i in ids]
        dt = [pol[p][i]["evac_time"] - pol[base][i]["evac_time"] for i in ids if pol[p][i]["success"] and pol[base][i]["success"]]
        a, b = bootstrap_ci(ds); c, d = bootstrap_ci(df); e, f = bootstrap_ci(dt)
        L.append(f"| {p} | {mean(ds):+.1f} [{a:+.1f}, {b:+.1f}] | {mean(df):+.3f} [{c:+.3f}, {d:+.3f}] | {mean(dt):+.1f} [{e:+.1f}, {f:+.1f}] |")
    return L


def summarize(rows: list[dict]) -> str:
    pol = by_policy(rows)
    order = [p for p in ("shortest_path", "static_risk", "dynamic_risk", "dynamic_perfect_perception", "oracle") if p in pol]
    ids_all = sorted(pol[order[0]])
    L = [f"Scenarios: {len(ids_all)} (paired: every policy sees the same scenario and detector noise)", "",
         "## All scenarios", ""] + _table(pol, order, ids_all)
    base = "shortest_path"
    dyn = [p for p in ("dynamic_risk", "dynamic_perfect_perception") if p in pol]
    if base in pol:
        L += [""] + _paired(pol, order, ids_all, base)
        if "static_risk" in pol and dyn:
            L += ["", "Is live re-planning better than planning once?", ""] + _paired(pol, dyn + ["static_risk"], ids_all, "static_risk")
        stress = [i for i in ids_all if pol[base][i]["fed"] >= STRESS_DOSE or not pol[base][i]["success"]]
        if stress:
            L += ["", f"## Hazard-relevant scenarios ({len(stress)} of {len(ids_all)}: the shortest route gets dose >= {STRESS_DOSE} or fails)", ""]
            L += _table(pol, order, stress) + [""] + _paired(pol, order, stress, base)
            if "static_risk" in pol and dyn:
                L += ["", "Live re-planning vs planning once (hazard-relevant scenarios):", ""] + _paired(pol, dyn + ["static_risk"], stress, "static_risk")
    if "oracle" in pol and "dynamic_risk" in pol:
        reg = [pol["dynamic_risk"][i]["fed"] - pol["oracle"][i]["fed"] for i in ids_all]
        lo, hi = bootstrap_ci(reg)
        L.append(f"\nRegret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): {mean(reg):.3f} [{lo:.3f}, {hi:.3f}]")
    return "\n".join(L)
