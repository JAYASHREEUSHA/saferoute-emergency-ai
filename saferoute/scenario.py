"""Ground-truth world for one simulated emergency.

Everything here is a deterministic function of time once the scenario is generated, and every
hazard is monotone (fire, smoke, crowds and obstacles only get worse). That property matters:
it makes the hindsight oracle in oracle.py exactly optimal.

Simplifying assumptions (state them in the report):
  * Fire spreads along corridors at a constant speed from one ignition junction.
  * Smoke travels faster than fire and ramps up to a maximum concentration.
  * Crowd hotspots ramp up to a fixed density; obstacles block a corridor permanently.
"""
from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field

from .graph import BuildingGraph


@dataclass
class ScenarioParams:
    """Defaults were chosen by ONE criterion, fixed before comparing policies: the hindsight oracle should
    be able to escape in roughly 90% of scenarios (otherwise many scenarios are unwinnable and say nothing
    about routing). Difficulty is varied systematically in the sensitivity experiments (Step 6)."""

    t_ignite_range: tuple[float, float] = (-60.0, -5.0)  # seconds relative to when the user starts moving
    ignition_radius_m: float | None = 45.0  # ignite within this walking distance of the user (None = anywhere)
    v_fire_range: tuple[float, float] = (0.1, 0.4)  # m/s fire front speed
    smoke_speed_ratio_range: tuple[float, float] = (1.5, 4.0)  # smoke speed = ratio * fire speed
    smoke_ramp_s: float = 30.0
    smoke_max_range: tuple[float, float] = (0.3, 0.9)
    base_density_prob: float = 0.5
    base_density_max: float = 0.3  # persons / m^2
    n_hotspots_range: tuple[int, int] = (0, 2)
    hotspot_density_range: tuple[float, float] = (1.5, 3.5)
    hotspot_onset_range: tuple[float, float] = (0.0, 40.0)
    hotspot_ramp_s: float = 20.0
    p_obstacle: float = 0.25
    obstacle_time_range: tuple[float, float] = (0.0, 40.0)


@dataclass
class Scenario:
    graph: BuildingGraph
    start: str
    fire_time: dict[str, float] = field(default_factory=dict)  # edge -> time it is on fire
    smoke_time: dict[str, float] = field(default_factory=dict)  # edge -> time smoke arrives
    smoke_ramp_s: float = 20.0
    smoke_max: float = 1.0
    base_density: dict[str, float] = field(default_factory=dict)
    hotspots: dict[str, tuple[float, float, float]] = field(default_factory=dict)  # edge -> (density, onset, ramp)
    obstacles: dict[str, float] = field(default_factory=dict)  # edge -> time it becomes blocked
    ignition_node: str | None = None
    t_ignite: float = 0.0

    def fire_on(self, eid: str, t: float) -> bool:
        return t >= self.fire_time.get(eid, math.inf)

    def smoke_level(self, eid: str, t: float) -> float:
        ts = self.smoke_time.get(eid, math.inf)
        if t < ts:
            return 0.0
        return self.smoke_max * min(1.0, (t - ts) / self.smoke_ramp_s)

    def blocked(self, eid: str, t: float) -> bool:
        return t >= self.obstacles.get(eid, math.inf)

    def impassable(self, eid: str, t: float) -> bool:
        """People never step into visible flames or a blocked corridor."""
        return self.fire_on(eid, t) or self.blocked(eid, t)

    def people(self, eid: str, t: float) -> float:
        e = self.graph.edges[eid]
        dens = self.base_density.get(eid, 0.0)
        if eid in self.hotspots:
            d, onset, ramp = self.hotspots[eid]
            frac = min(1.0, max(0.0, (t - onset) / ramp))
            dens = dens + (d - dens) * frac
        return dens * e.area


def _dist_from(graph: BuildingGraph, src: str) -> dict[str, float]:
    dist = {n: math.inf for n in graph.nodes}
    dist[src] = 0.0
    heap = [(0.0, src)]
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist[n]:
            continue
        for nb, eid in graph.adj[n]:
            nd = d + graph.edges[eid].length
            if nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return dist


def generate_scenario(
    graph: BuildingGraph, rng: random.Random, params: ScenarioParams | None = None, start: str | None = None
) -> Scenario:
    p = params or ScenarioParams()
    non_exit = [n for n, node in graph.nodes.items() if node.kind != "exit"]
    start = start or rng.choice(non_exit)
    candidates = [n for n in non_exit if n != start]
    if p.ignition_radius_m is not None:
        d_start = _dist_from(graph, start)
        near = [n for n in candidates if d_start[n] <= p.ignition_radius_m]
        candidates = near or candidates
    ignition = rng.choice(candidates)

    t0 = rng.uniform(*p.t_ignite_range)
    v_fire = rng.uniform(*p.v_fire_range)
    v_smoke = v_fire * rng.uniform(*p.smoke_speed_ratio_range)
    dist = _dist_from(graph, ignition)

    fire_time, smoke_time = {}, {}
    for eid, e in graph.edges.items():
        d = min(dist[e.u], dist[e.v])  # an edge is reached when its nearer end is reached
        fire_time[eid] = t0 + d / v_fire
        smoke_time[eid] = t0 + d / v_smoke

    base = {
        eid: rng.uniform(0.0, p.base_density_max)
        for eid in graph.edges
        if rng.random() < p.base_density_prob
    }
    n_hot = rng.randint(*p.n_hotspots_range)
    hotspots = {
        eid: (rng.uniform(*p.hotspot_density_range), rng.uniform(*p.hotspot_onset_range), p.hotspot_ramp_s)
        for eid in rng.sample(sorted(graph.edges), min(n_hot, len(graph.edges)))
    }
    obstacles = {}
    if rng.random() < p.p_obstacle:
        obstacles[rng.choice(sorted(graph.edges))] = rng.uniform(*p.obstacle_time_range)

    return Scenario(
        graph=graph, start=start, fire_time=fire_time, smoke_time=smoke_time,
        smoke_ramp_s=p.smoke_ramp_s, smoke_max=rng.uniform(*p.smoke_max_range),
        base_density=base, hotspots=hotspots, obstacles=obstacles,
        ignition_node=ignition, t_ignite=t0,
    )
