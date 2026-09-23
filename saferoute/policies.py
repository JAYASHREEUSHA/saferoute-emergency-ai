"""Routing policies compared in the experiments.

All policies share one interface: plan(node, t, perception, excluded) -> node path or None.
`excluded` holds corridors the walker can see are impassable right now (fire / obstacle), so every
policy, including the baselines, avoids visible flames. That keeps the shortest-path baseline honest.
"""
from __future__ import annotations

import copy
import math

from .graph import BuildingGraph
from .planner import RoutePlanner, astar, best_route
from .risk import EdgeObservation, RiskConfig


class Policy:
    name = "base"

    def reset(self, graph: BuildingGraph) -> None:
        self.graph = graph

    def plan(self, node: str, t: float, perception, excluded: set[str]) -> list[str] | None:
        raise NotImplementedError


class ShortestPathPolicy(Policy):
    """Hazard-blind navigation: nearest exit by distance, replanned only around visibly blocked corridors."""

    name = "shortest_path"

    def plan(self, node, t, perception, excluded):
        g = self.graph
        best_path, best_len = None, math.inf
        for ex in g.exits:
            found = astar(
                g, node, ex,
                lambda e: math.inf if e.id in excluded else e.length,
                lambda n, ex=ex: g.euclid(n, ex),
            )
            if found and found[2] < best_len:
                best_path, best_len = found[0], found[2]
        return best_path


class StaticRiskPolicy(Policy):
    """Risk-aware route computed ONCE from the observations at t=0, then followed (no live updates)."""

    name = "static_risk"

    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg

    def reset(self, graph):
        super().reset(graph)
        self.obs0: dict[str, EdgeObservation] | None = None
        self.path: list[str] = []

    def plan(self, node, t, perception, excluded):
        if self.obs0 is None:
            self.obs0 = copy.deepcopy(perception.observations())
        if not excluded and self.path and node in self.path:
            return self.path[self.path.index(node):]
        obs = dict(self.obs0)
        for eid in excluded:
            obs[eid] = EdgeObservation(p_block=1.0)
        opt = best_route(self.graph, obs, node, self.cfg)
        if opt is None:
            return None
        if not excluded:
            self.path = opt.path
        return opt.path


class DynamicRiskPolicy(Policy):
    """The proposed method: re-plan at every junction from the latest observations, with hysteresis."""

    name = "dynamic_risk"

    def __init__(self, cfg: RiskConfig, name: str | None = None):
        self.cfg = cfg
        if name:
            self.name = name

    def reset(self, graph):
        super().reset(graph)
        self.planner = RoutePlanner(graph, self.cfg)

    def plan(self, node, t, perception, excluded):
        obs = dict(perception.observations())
        for eid in excluded:
            obs[eid] = EdgeObservation(p_block=1.0)
        decision = self.planner.update(obs, node)
        return decision.recommended.path if decision.recommended else None
