"""Agent simulation on the building graph.

One evacuee walks node to node. At every junction the policy proposes a route from what it
*believes* (perception); the world then applies ground truth: crowd and smoke slow the walker,
smoke and fire accumulate a dose, and nobody steps into a corridor that is visibly on fire or blocked.

The dose is a simplified incapacitation proxy (a Fractional-Effective-Dose-style counter), NOT a
validated toxicity model. Its constants are assumptions; the report should include a sensitivity check.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from .graph import BuildingGraph, Edge
from .risk import RiskConfig, walking_speed
from .scenario import Scenario


@dataclass
class SimConfig:
    fed_smoke_per_s: float = 1 / 60  # dose per second in full-density smoke (incapacitated at dose >= 1)
    fed_fire_per_s: float = 1 / 10  # dose per second inside a burning corridor
    smoke_speed_loss: float = 0.5  # walking speed lost in full-density smoke
    smoke_visible_threshold: float = 0.3  # smoke level counted as "time in smoke"
    dt: float = 1.0
    t_max: float = 300.0


@dataclass
class Outcome:
    success: bool = False
    evac_time: float | None = None
    fed: float = 0.0  # final dose, capped at 1.0
    incapacitated: bool = False
    timed_out: bool = False
    smoke_time: float = 0.0
    fire_time: float = 0.0
    wait_time: float = 0.0
    path_length: float = 0.0
    n_reroutes: int = 0
    n_plans: int = 0
    plan_ms: float = 0.0
    path: list[str] = field(default_factory=list)


@dataclass
class TraverseResult:
    t_end: float
    fed_end: float
    smoke_time: float
    fire_time: float
    incapacitated: bool


def traverse(scn: Scenario, edge: Edge, t: float, fed: float, scfg: SimConfig, wcfg: RiskConfig) -> TraverseResult:
    """Walk one corridor starting at time t with accumulated dose `fed`. Shared with the oracle."""
    s = 0.0
    smoke_t = fire_t = 0.0
    while s < edge.length:
        smoke = scn.smoke_level(edge.id, t)
        fire = scn.fire_on(edge.id, t)
        rho = scn.people(edge.id, t) / edge.area
        v = max(wcfg.v_min, walking_speed(rho, wcfg) * (1.0 - scfg.smoke_speed_loss * smoke))
        step = min(scfg.dt, (edge.length - s) / v)
        fed += (scfg.fed_smoke_per_s * smoke + (scfg.fed_fire_per_s if fire else 0.0)) * step
        s += v * step
        t += step
        if smoke > scfg.smoke_visible_threshold:
            smoke_t += step
        if fire:
            fire_t += step
        if fed >= 1.0:
            return TraverseResult(t, fed, smoke_t, fire_t, True)
        if t >= scfg.t_max:
            break
    return TraverseResult(t, fed, smoke_t, fire_t, False)


def simulate(graph: BuildingGraph, scn: Scenario, policy, perception, scfg: SimConfig, wcfg: RiskConfig) -> Outcome:
    policy.reset(graph)
    out = Outcome(path=[scn.start])
    t, node, fed = 0.0, scn.start, 0.0
    last_target: str | None = None
    perception.advance_to(0)

    while True:
        if t >= scfg.t_max:
            out.timed_out = True
            break
        if node in graph.exits:
            out.success, out.evac_time = True, t
            break

        perception.advance_to(math.floor(t))
        excluded: set[str] = set()
        nxt = target = edge = None
        while True:  # ask for a plan; skip corridors that are visibly impassable right now
            t0 = time.perf_counter()
            plan = policy.plan(node, t, perception, excluded)
            out.plan_ms += (time.perf_counter() - t0) * 1000.0
            out.n_plans += 1
            if not plan or len(plan) < 2:
                break
            edge = graph.edge_between(node, plan[1])
            if edge is None:
                raise ValueError(f"policy {policy.name} returned a non-adjacent step {node}->{plan[1]}")
            if scn.impassable(edge.id, t):
                if edge.id in excluded:  # policy insists on a corridor we already know is blocked
                    break
                excluded.add(edge.id)
                continue
            nxt, target = plan[1], plan[-1]
            break

        if nxt is None:  # no usable route: wait at the junction (smoke still accumulates)
            smoke = max((scn.smoke_level(eid, t) for _, eid in graph.adj[node]), default=0.0)
            fed += scfg.fed_smoke_per_s * smoke * scfg.dt
            if smoke > scfg.smoke_visible_threshold:
                out.smoke_time += scfg.dt
            t += scfg.dt
            out.wait_time += scfg.dt
            if fed >= 1.0:
                out.incapacitated = True
                break
            continue

        if last_target is not None and target != last_target:
            out.n_reroutes += 1
        last_target = target

        r = traverse(scn, edge, t, fed, scfg, wcfg)
        t, fed = r.t_end, r.fed_end
        out.smoke_time += r.smoke_time
        out.fire_time += r.fire_time
        out.path_length += edge.length
        if r.incapacitated:
            out.incapacitated = True
            break
        node = nxt
        out.path.append(node)

    out.fed = 1.0 if out.incapacitated else min(1.0, fed)
    return out
