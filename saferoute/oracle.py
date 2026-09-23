"""Hindsight oracle: the best any routing policy could have done in a given scenario.

Because every hazard is monotone in time (see scenario.py), arriving earlier with a lower dose
dominates arriving later with a higher dose. A Pareto label-setting search over (time, dose) at
each junction is therefore exact. It uses the same physics (traverse) as the simulator.
The oracle knows the entire future, so it is an upper bound, not a deployable policy.
"""
from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field

from .graph import BuildingGraph
from .risk import RiskConfig
from .scenario import Scenario
from .sim import Outcome, SimConfig, traverse


@dataclass
class _Label:
    t: float
    fed: float
    smoke_t: float
    fire_t: float
    length: float
    path: list[str] = field(default_factory=list)
    alive: bool = True


def oracle_outcome(graph: BuildingGraph, scn: Scenario, scfg: SimConfig, wcfg: RiskConfig) -> Outcome:
    labels: dict[str, list[_Label]] = {n: [] for n in graph.nodes}
    first = _Label(0.0, 0.0, 0.0, 0.0, 0.0, [scn.start])
    labels[scn.start].append(first)
    counter = itertools.count()
    heap = [(0.0, next(counter), first)]

    while heap:
        _, _, lab = heapq.heappop(heap)
        if not lab.alive:
            continue
        node = lab.path[-1]
        if node in graph.exits:
            continue
        for nb, eid in graph.adj[node]:
            if scn.impassable(eid, lab.t):
                continue
            edge = graph.edges[eid]
            r = traverse(scn, edge, lab.t, lab.fed, scfg, wcfg)
            if r.incapacitated or r.t_end >= scfg.t_max:
                continue
            if any(o.t <= r.t_end and o.fed <= r.fed_end for o in labels[nb] if o.alive):
                continue  # dominated
            for o in labels[nb]:
                if o.alive and r.t_end <= o.t and r.fed_end <= o.fed:
                    o.alive = False
            new = _Label(r.t_end, r.fed_end, lab.smoke_t + r.smoke_time, lab.fire_t + r.fire_time,
                         lab.length + edge.length, lab.path + [nb])
            labels[nb].append(new)
            heapq.heappush(heap, (new.t, next(counter), new))

    finals = [lab for ex in graph.exits for lab in labels[ex] if lab.alive]
    if not finals:
        return Outcome(success=False, fed=1.0, path=[scn.start])
    best = min(finals, key=lambda l: (l.fed, l.t))
    return Outcome(
        success=True, evac_time=best.t, fed=min(1.0, best.fed), smoke_time=best.smoke_t,
        fire_time=best.fire_t, path_length=best.length, path=best.path,
    )
