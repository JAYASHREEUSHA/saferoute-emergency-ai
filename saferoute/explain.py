"""Explanations built from the real cost breakdown (no LLM involved in decisions).

Every sentence is generated from numbers the planner actually used, so the
explanation cannot disagree with the decision."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .graph import BuildingGraph
from .planner import Decision, Observations, RouteOption, shortest_by_distance
from .risk import RiskConfig, dominant_hazard

_COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]


def risk_level(opt: RouteOption) -> str:
    if not opt.reachable:
        return "Unreachable"
    if not opt.feasible:
        return "Blocked"
    if opt.route_risk < 0.2:
        return "Low"
    if opt.route_risk < 0.5:
        return "Medium"
    return "High"


def _compass(dx: float, dy: float) -> str:
    angle = (math.degrees(math.atan2(dx, dy)) + 360) % 360  # 0 = north, clockwise
    return _COMPASS[int((angle + 22.5) // 45) % 8]


def next_instruction(graph: BuildingGraph, opt: RouteOption) -> str:
    if len(opt.path) < 2:
        return ""
    a, b = graph.nodes[opt.path[0]], graph.nodes[opt.path[1]]
    edge = graph.edges[opt.edge_ids[0]]
    return f"Head {_compass(b.x - a.x, b.y - a.y)} toward {graph.label(b.id)} for {edge.length:.0f} m."


@dataclass
class Explanation:
    headline: str
    voice: str
    reasons: list[str] = field(default_factory=list)
    table: list[dict] = field(default_factory=list)


def _blocked_reason(opt: RouteOption, graph: BuildingGraph, obs: Observations, cfg: RiskConfig) -> str:
    parts = []
    for eid in opt.blocked_edges:
        name, p = dominant_hazard(obs.get(eid), cfg)
        parts.append(f"{name} on {graph.edges[eid].label or eid} (p={p:.2f})")
    return "; ".join(parts)


def _drivers(o: RouteOption, rec: RouteOption) -> str:
    """Why option `o` costs more than the recommended route `rec`, from the cost components."""
    parts = []
    if o.crowd_delay - rec.crowd_delay > 1:
        parts.append(f"crowd delay +{o.crowd_delay - rec.crowd_delay:.0f} s")
    if o.hazard_penalty - rec.hazard_penalty > 1:
        parts.append(f"hazard penalty +{o.hazard_penalty - rec.hazard_penalty:.0f} s")
    if o.free_flow_time - rec.free_flow_time > 1:
        parts.append(f"walking time +{o.free_flow_time - rec.free_flow_time:.0f} s")
    return ", ".join(parts) or "slightly higher cost"


def _previous_route_cause(prev: RouteOption, graph: BuildingGraph, obs: Observations, cfg: RiskConfig) -> str:
    """Main reason the previously recommended route stopped being the best one."""
    if prev.blocked_edges:
        return _blocked_reason(prev, graph, obs, cfg)
    if prev.crowd_delay > prev.hazard_penalty and prev.crowd_edge is not None:
        e = graph.edges[prev.crowd_edge]
        return f"heavy crowding on {e.label or e.id} ({prev.crowd_density:.1f} people/m2)"
    if prev.worst_edge is not None:
        name, _ = dominant_hazard(obs.get(prev.worst_edge), cfg)
        return f"{name} on {graph.edges[prev.worst_edge].label or prev.worst_edge}"
    return ""


def explain(decision: Decision, graph: BuildingGraph, obs: Observations, cfg: RiskConfig) -> Explanation:
    rec = decision.recommended
    opts = {o.exit_id: o for o in decision.options}
    lab = graph.label

    # ---- table for the dashboard (one row per exit) --------------------------
    table = []
    for o in decision.options:
        table.append(
            {
                "exit": lab(o.exit_id),
                "status": risk_level(o),
                "distance_m": round(o.length_m, 1) if o.reachable else None,
                "travel_time_s": round(o.travel_time, 1) if o.reachable else None,
                "route_risk": round(o.route_risk, 2) if o.reachable else None,
                "cost": round(o.total_cost, 1) if (o.reachable and o.feasible) else None,
                "recommended": bool(rec and o.exit_id == rec.exit_id),
            }
        )

    if decision.event == "arrived":
        return Explanation("You have reached an exit.", "You have reached the exit.", [], table)

    if rec is None:
        msg = "No route to any exit found. Follow official alarms and staff instructions."
        return Explanation(msg, msg, [], table)

    # ---- per-exit reasons ------------------------------------------------------
    reasons: list[str] = []
    short_exit, short_len = shortest_by_distance(graph, decision.current_node)

    if decision.no_safe_route:
        reasons.append(
            f"No exit is free of hard hazards. {lab(rec.exit_id)} has the lowest combined cost "
            f"but crosses: {_blocked_reason(rec, graph, obs, cfg)}."
        )
    else:
        line = (
            f"{lab(rec.exit_id)} selected: lowest overall cost ({rec.total_cost:.0f} s-equivalent), "
            f"route risk {rec.route_risk:.0%}."
        )
        if short_exit and short_exit != rec.exit_id:
            closest = opts[short_exit]
            extra = rec.length_m - short_len
            if not closest.feasible:
                line += f" It is {extra:.0f} m longer than {lab(short_exit)} (closest by distance), which is blocked."
            else:
                line += (
                    f" It is {extra:.0f} m longer than {lab(short_exit)} (closest by distance), "
                    f"which costs {closest.total_cost - rec.total_cost:.0f} more ({_drivers(closest, rec)})."
                )
        reasons.append(line)

    for o in decision.options:
        if o.exit_id == rec.exit_id:
            continue
        if not o.reachable:
            reasons.append(f"{lab(o.exit_id)} rejected: no route available.")
        elif not o.feasible:
            reasons.append(f"{lab(o.exit_id)} rejected: {_blocked_reason(o, graph, obs, cfg)}.")
        else:
            reasons.append(
                f"{lab(o.exit_id)} not selected: costs {o.total_cost - rec.total_cost:.0f} more ({_drivers(o, rec)})."
            )

    # ---- headline / voice ------------------------------------------------------
    if decision.event == "initial":
        headline = f"Recommended exit: {lab(rec.exit_id)}."
    elif decision.event == "keep":
        headline = f"Continue toward {lab(rec.exit_id)}."
    elif decision.event == "no_safe_route":
        headline = (
            f"Warning: no safe route available. Least-risk option: {lab(rec.exit_id)}. "
            "Follow official alarms and staff instructions."
        )
    else:  # reroute_blocked / reroute_better
        prev = opts.get(decision.previous_exit or "")
        cause = _previous_route_cause(prev, graph, obs, cfg) if (prev is not None and prev.reachable) else ""
        cause = cause or "conditions changed"
        headline = (
            f"Warning: {cause}. Your previous route to {lab(decision.previous_exit or '?')} "
            f"is no longer recommended. Recalculating... Now recommending {lab(rec.exit_id)}."
        )

    voice = f"{headline} {next_instruction(graph, rec)}".strip()
    return Explanation(headline, voice, reasons, table)
