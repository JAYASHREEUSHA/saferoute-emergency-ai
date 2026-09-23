"""Route planning: A* over the risk-weighted graph, per-exit evaluation, and a stateful
planner with hysteresis so the recommendation does not flip-flop on noisy detections."""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Callable

from .graph import BuildingGraph, Edge
from .risk import EdgeObservation, RiskConfig, dominant_hazard, edge_cost

Observations = dict[str, EdgeObservation]


# --------------------------------------------------------------------------- search
def astar(
    graph: BuildingGraph,
    start: str,
    goal: str,
    cost_fn: Callable[[Edge], float],
    heuristic: Callable[[str], float] | None = None,
) -> tuple[list[str], list[str], float] | None:
    """A* search. Returns (node path, edge ids, cost) or None if unreachable.

    `heuristic=None` degrades to Dijkstra (used in tests to verify optimality).
    """
    h = heuristic or (lambda n: 0.0)
    counter = 0
    heap: list[tuple[float, int, str]] = [(h(start), counter, start)]
    g = {start: 0.0}
    parent: dict[str, tuple[str, str]] = {}
    closed: set[str] = set()

    while heap:
        _, _, node = heapq.heappop(heap)
        if node == goal:
            nodes, edges = [goal], []
            while nodes[-1] != start:
                prev, eid = parent[nodes[-1]]
                nodes.append(prev)
                edges.append(eid)
            return nodes[::-1], edges[::-1], g[goal]
        if node in closed:
            continue
        closed.add(node)
        for nb, eid in graph.adj[node]:
            c = cost_fn(graph.edges[eid])
            if math.isinf(c):
                continue
            new_g = g[node] + c
            if new_g < g.get(nb, math.inf):
                g[nb] = new_g
                parent[nb] = (node, eid)
                counter += 1
                heapq.heappush(heap, (new_g + h(nb), counter, nb))
    return None


# --------------------------------------------------------------------------- options
@dataclass
class RouteOption:
    exit_id: str
    path: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    length_m: float = math.inf
    free_flow_time: float = math.inf
    crowd_delay: float = 0.0
    hazard_penalty: float = 0.0
    blocked_penalty: float = 0.0
    total_cost: float = math.inf
    route_risk: float = 1.0  # 1 - prod(1 - r_e); 1.0 if the route crosses a blocked edge
    feasible: bool = False  # False => route crosses a hard-blocked edge (or is unreachable)
    reachable: bool = False
    blocked_edges: list[str] = field(default_factory=list)
    worst_edge: str | None = None  # edge with highest hazard risk on the route
    crowd_edge: str | None = None  # edge with the largest crowd delay on the route
    crowd_density: float = 0.0  # persons / m^2 on that edge

    @property
    def travel_time(self) -> float:
        return self.free_flow_time + self.crowd_delay


def _build_option(
    graph: BuildingGraph, obs: Observations, start: str, exit_id: str, cfg: RiskConfig, relax: bool
) -> RouteOption | None:
    costs = {eid: edge_cost(e, obs.get(eid), cfg, relax=relax) for eid, e in graph.edges.items()}

    def cost_fn(e: Edge) -> float:
        c = costs[e.id]
        return math.inf if (c.blocked and not relax) else c.total

    h = lambda n: graph.euclid(n, exit_id) / cfg.v_free  # admissible: every edge costs >= L / v_free
    found = astar(graph, start, exit_id, cost_fn, h)
    if found is None:
        return None
    path, edge_ids, _ = found

    seg = [costs[eid] for eid in edge_ids]
    blocked_edges = [eid for eid in edge_ids if costs[eid].blocked]
    survive = 1.0
    for c in seg:
        survive *= 1.0 - c.risk
    worst = max(edge_ids, key=lambda eid: costs[eid].risk, default=None)
    if worst is not None and costs[worst].risk <= 0:
        worst = None
    crowd = max(edge_ids, key=lambda eid: costs[eid].crowd_delay, default=None)
    if crowd is not None and costs[crowd].crowd_delay <= 1.0:
        crowd = None
    return RouteOption(
        exit_id=exit_id,
        path=path,
        edge_ids=edge_ids,
        length_m=sum(graph.edges[eid].length for eid in edge_ids),
        free_flow_time=sum(c.free_flow_time for c in seg),
        crowd_delay=sum(c.crowd_delay for c in seg),
        hazard_penalty=sum(c.hazard_penalty for c in seg),
        blocked_penalty=sum(c.blocked_penalty for c in seg),
        total_cost=sum(c.total for c in seg),
        route_risk=1.0 if blocked_edges else 1.0 - survive,
        feasible=not blocked_edges,
        reachable=True,
        blocked_edges=blocked_edges,
        worst_edge=worst,
        crowd_edge=crowd,
        crowd_density=costs[crowd].density if crowd else 0.0,
    )


def evaluate_exits(graph: BuildingGraph, obs: Observations, start: str, cfg: RiskConfig) -> list[RouteOption]:
    """Best route to every exit. Exits that can only be reached through hard-blocked
    edges are returned with feasible=False (route priced with `relax`) so they can be explained."""
    options = []
    for ex in graph.exits:
        opt = _build_option(graph, obs, start, ex, cfg, relax=False)
        if opt is None:
            opt = _build_option(graph, obs, start, ex, cfg, relax=True)
        options.append(opt or RouteOption(exit_id=ex))
    return options


def shortest_by_distance(graph: BuildingGraph, start: str) -> tuple[str, float]:
    """Exit that is closest by pure distance, ignoring every hazard (the baseline policy)."""
    best_exit, best_len = "", math.inf
    for ex in graph.exits:
        found = astar(graph, start, ex, lambda e: e.length, lambda n: graph.euclid(n, ex))
        if found and found[2] < best_len:
            best_exit, best_len = ex, found[2]
    return best_exit, best_len


# --------------------------------------------------------------------------- planner
@dataclass
class Decision:
    event: str  # initial | keep | reroute_blocked | reroute_better | no_safe_route | arrived
    current_node: str
    recommended: RouteOption | None
    options: list[RouteOption]
    previous_exit: str | None = None
    no_safe_route: bool = False

    @property
    def changed(self) -> bool:
        return self.event in ("initial", "reroute_blocked", "reroute_better", "no_safe_route")


class RoutePlanner:
    """Stateful planner. Call update() every time observations or the user position change."""

    def __init__(self, graph: BuildingGraph, cfg: RiskConfig | None = None):
        self.graph = graph
        self.cfg = cfg or RiskConfig()
        self.current_exit: str | None = None

    def reset(self) -> None:
        self.current_exit = None

    def update(self, obs: Observations, current_node: str) -> Decision:
        prev = self.current_exit
        if current_node in self.graph.exits:
            return Decision("arrived", current_node, None, [], previous_exit=prev)

        options = evaluate_exits(self.graph, obs, current_node, self.cfg)
        feasible = [o for o in options if o.feasible]

        if not feasible:
            # Every exit is blocked or unreachable: least-bad route, with a warning.
            reachable = [o for o in options if o.reachable]
            if not reachable:
                return Decision("no_safe_route", current_node, None, options, prev, no_safe_route=True)
            best = min(reachable, key=lambda o: o.total_cost)
            self.current_exit = best.exit_id
            return Decision("no_safe_route", current_node, best, options, prev, no_safe_route=True)

        best = min(feasible, key=lambda o: o.total_cost)
        if prev is None:
            self.current_exit = best.exit_id
            return Decision("initial", current_node, best, options, prev)

        current = next((o for o in feasible if o.exit_id == prev), None)
        if current is None:  # current target became blocked / unreachable
            self.current_exit = best.exit_id
            return Decision("reroute_blocked", current_node, best, options, prev)
        if best.exit_id != current.exit_id and best.total_cost < current.total_cost - self.cfg.switch_margin_s:
            self.current_exit = best.exit_id
            return Decision("reroute_better", current_node, best, options, prev)
        return Decision("keep", current_node, current, options, prev)


def dominant_on_route(opt: RouteOption, obs: Observations, cfg: RiskConfig) -> tuple[str, float] | None:
    if opt.worst_edge is None:
        return None
    return dominant_hazard(obs.get(opt.worst_edge), cfg)


def best_route(graph: BuildingGraph, obs: Observations, start: str, cfg: RiskConfig) -> RouteOption | None:
    """One-shot risk-aware route: cheapest feasible exit, else the least-bad reachable one."""
    options = evaluate_exits(graph, obs, start, cfg)
    pool = [o for o in options if o.feasible] or [o for o in options if o.reachable]
    return min(pool, key=lambda o: o.total_cost) if pool else None
