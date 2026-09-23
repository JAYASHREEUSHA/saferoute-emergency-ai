"""Step 6: sensitivity experiments. Each function runs the SAME paired-scenario design as
saferoute.experiment.run_experiment, varying one thing at a time, and returns rows a script
can render as a markdown table. No plotting library is used (stdlib only, per project policy);
tables are picked over charts to keep the dependency footprint the same as Steps 1-2.
"""
from __future__ import annotations

import random
from dataclasses import replace

from .experiment import bootstrap_ci, by_policy, default_specs, mean, percentile, run_experiment
from .graph import BuildingGraph
from .perception import PerceptionConfig
from .policies import DynamicRiskPolicy, ShortestPathPolicy, StaticRiskPolicy
from .risk import RiskConfig
from .scenario import ScenarioParams
from .sim import SimConfig


def _dynamic_vs_shortest(rows: list[dict]) -> dict:
    """Collapse one run_experiment() result into the numbers a sweep table needs."""
    pol = by_policy(rows)
    sp, dr = pol.get("shortest_path", {}), pol.get("dynamic_risk", {})
    ids = sorted(set(sp) & set(dr))
    d_dose = [dr[i]["fed"] - sp[i]["fed"] for i in ids]
    d_succ = [100 * (dr[i]["success"] - sp[i]["success"]) for i in ids]
    lo, hi = bootstrap_ci(d_dose)
    return dict(
        n=len(ids),
        dyn_success=100 * mean(dr[i]["success"] for i in ids),
        dyn_dose=mean(dr[i]["fed"] for i in ids),
        d_dose=mean(d_dose), d_dose_lo=lo, d_dose_hi=hi,
        d_success=mean(d_succ),
    )


# --------------------------------------------------------------------------- 1. lambda sweep
def lambda_sweep(graph: BuildingGraph, lambdas: list[float], n: int, seed: int, pcfg: PerceptionConfig | None = None) -> list[dict]:
    """How the hazard penalty lambda trades off evacuation time against hazard exposure.
    Same scenarios are reused across lambda values (only the policies' risk_cfg changes)."""
    pcfg = pcfg or PerceptionConfig()
    out = []
    for lam in lambdas:
        risk_cfg = RiskConfig(lam=lam)
        rows = run_experiment(graph, n, seed, default_specs(risk_cfg, pcfg), wcfg=RiskConfig())
        r = _dynamic_vs_shortest(rows)
        pol = by_policy(rows)["dynamic_risk"]
        ts = [v["evac_time"] for v in pol.values() if v["success"]]
        out.append(dict(lam=lam, mean_time=mean(ts), p95_time=percentile(ts, 0.95), **r))
    return out


def render_lambda_sweep(rows: list[dict]) -> str:
    L = [
        "| lambda | dynamic success % | dynamic mean dose | dynamic mean time (s) | dose vs shortest_path [95% CI] |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        L.append(
            f"| {r['lam']:g} | {r['dyn_success']:.1f} | {r['dyn_dose']:.3f} | {r['mean_time']:.1f} "
            f"| {r['d_dose']:+.3f} [{r['d_dose_lo']:+.3f}, {r['d_dose_hi']:+.3f}] |"
        )
    return "\n".join(L)


# --------------------------------------------------------------------------- 2. perception sweep
def perception_sweep(graph: BuildingGraph, configs: dict[str, PerceptionConfig], n: int, seed: int, risk_cfg: RiskConfig | None = None) -> list[dict]:
    """How much of dynamic_risk's advantage survives as the detector gets worse."""
    risk_cfg = risk_cfg or RiskConfig()
    out = []
    for name, pcfg in configs.items():
        rows = run_experiment(graph, n, seed, default_specs(risk_cfg, pcfg), wcfg=RiskConfig())
        out.append(dict(name=name, mode=pcfg.mode, recall=pcfg.recall, fp=pcfg.fp_rate, latency=pcfg.latency_s, **_dynamic_vs_shortest(rows)))
    return out


def render_perception_sweep(rows: list[dict]) -> str:
    L = [
        "| detector | recall | fp rate | latency (s) | dynamic success % | dose vs shortest_path [95% CI] |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r.get("mode") == "perfect":
            recall_s, fp_s, lat_s = "n/a", "n/a", "n/a"
        else:
            recall_s, fp_s, lat_s = f"{r['recall']:.2f}", f"{r['fp']:.3f}", f"{r['latency']:.1f}"
        L.append(f"| {r['name']} | {recall_s} | {fp_s} | {lat_s} | {r['dyn_success']:.1f} | {r['d_dose']:+.3f} [{r['d_dose_lo']:+.3f}, {r['d_dose_hi']:+.3f}] |")
    return "\n".join(L)


# --------------------------------------------------------------------------- 3. difficulty sweep
def difficulty_sweep(graph: BuildingGraph, settings: dict[str, ScenarioParams], n: int, seed: int, pcfg: PerceptionConfig | None = None) -> list[dict]:
    """Does the result hold up as the emergency gets harder (faster fire, later warning)?
    Also reports the oracle's own success rate, since a setting where the oracle can't escape
    either says nothing about routing quality."""
    pcfg = pcfg or PerceptionConfig()
    out = []
    for name, params in settings.items():
        rows = run_experiment(graph, n, seed, default_specs(RiskConfig(), pcfg), params=params, wcfg=RiskConfig())
        pol = by_policy(rows)
        oracle_succ = 100 * mean(v["success"] for v in pol["oracle"].values())
        out.append(dict(name=name, oracle_success=oracle_succ, **_dynamic_vs_shortest(rows)))
    return out


def render_difficulty_sweep(rows: list[dict]) -> str:
    L = [
        "| difficulty | oracle success % | dynamic success % | dose vs shortest_path [95% CI] |",
        "|---|---|---|---|",
    ]
    for r in rows:
        L.append(f"| {r['name']} | {r['oracle_success']:.1f} | {r['dyn_success']:.1f} | {r['d_dose']:+.3f} [{r['d_dose_lo']:+.3f}, {r['d_dose_hi']:+.3f}] |")
    return "\n".join(L)


# --------------------------------------------------------------------------- 4. ablations
def ablation_runs(graph: BuildingGraph, n: int, seed: int) -> list[dict]:
    """Turn one mechanism off at a time and measure the cost, on the SAME scenarios.
    - no_hysteresis: switch_margin_s=0 (reroute the instant a cheaper option appears)
    - no_crowd_term: crowd never raises cost (severity of the crowd term zeroed via a huge
      rho_max, so walking speed stays near free-flow regardless of density)
    - perfect_perception: ground-truth hazards, no latency (isolates the routing logic
      itself from detector noise; already reported in the main experiment, repeated here
      for a side-by-side ablation table)
    """
    risk_cfg = RiskConfig()
    pcfg = PerceptionConfig()
    variants = {
        "dynamic_risk (full)": (risk_cfg, pcfg, DynamicRiskPolicy),
        "no_hysteresis": (replace(risk_cfg, switch_margin_s=0.0), pcfg, DynamicRiskPolicy),
        "no_crowd_term": (replace(risk_cfg, rho_max=1e6), pcfg, DynamicRiskPolicy),
        "perfect_perception": (risk_cfg, replace(pcfg, mode="perfect", latency_s=0.0), DynamicRiskPolicy),
    }
    out = []
    for name, (rc, pc, PolicyCls) in variants.items():
        specs = [s for s in default_specs(rc, pc) if s.name == "dynamic_risk"]
        specs[0] = replace(specs[0], name=name)
        specs.append([s for s in default_specs(rc, pc) if s.name == "shortest_path"][0])
        rows = run_experiment(graph, n, seed, specs, wcfg=RiskConfig())
        pol = by_policy(rows)
        v, base = pol[name], pol["shortest_path"]
        ids = sorted(set(v) & set(base))
        d_dose = [v[i]["fed"] - base[i]["fed"] for i in ids]
        lo, hi = bootstrap_ci(d_dose)
        out.append(
            dict(
                name=name, success=100 * mean(v[i]["success"] for i in ids), dose=mean(v[i]["fed"] for i in ids),
                d_dose=mean(d_dose), d_dose_lo=lo, d_dose_hi=hi,
                reroutes=mean(v[i]["n_reroutes"] for i in ids),
            )
        )
    return out


def render_ablations(rows: list[dict]) -> str:
    L = ["| variant | success % | mean dose | dose vs shortest_path [95% CI] | mean reroutes |", "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['name']} | {r['success']:.1f} | {r['dose']:.3f} | {r['d_dose']:+.3f} [{r['d_dose_lo']:+.3f}, {r['d_dose_hi']:+.3f}] | {r['reroutes']:.2f} |")
    return "\n".join(L)
