"""Risk model.

Design (see README):
  * Crowd is converted to *travel time* with a pedestrian fundamental diagram
    (Weidmann), so it needs no hand-tuned weight.
  * Hazards are probabilities (later: calibrated, temporally smoothed detector confidence).
  * Edge cost      c_e = t_e + lambda * r_e     (seconds-equivalent)
      t_e    = L_e / v(rho_e)                    travel time incl. crowd slowdown
      r_e    = 1 - (1-s_f p_fire)(1-s_s p_smoke)(1-s_b p_block)
      lambda = seconds of delay we accept to avoid a certain hazard
  * Fire / blocked probability above a threshold makes the edge impassable (hard constraint).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .graph import Edge


@dataclass
class RiskConfig:
    # Pedestrian fundamental diagram (Weidmann): free-flow speed and jam density.
    v_free: float = 1.34  # m/s
    rho_max: float = 5.4  # persons / m^2
    gamma: float = 1.913
    v_min: float = 0.05  # m/s floor so travel time stays finite

    # Hazard penalty and hard constraints. These are starting values to be
    # calibrated with the simulator (lambda sweep -> Pareto front), not truths.
    lam: float = 60.0  # seconds-equivalent penalty for a certain hazard
    tau_fire: float = 0.6  # p_fire above this => edge impassable
    tau_block: float = 0.6  # p_block above this => edge impassable
    severity: dict = field(default_factory=lambda: {"fire": 1.0, "smoke": 1.0, "blocked": 1.0})
    unknown_prior_risk: float = 0.05  # risk assumed on edges with no camera coverage

    # Used only when NO exit is safe: blocked edges become very expensive, not forbidden.
    blocked_penalty_s: float = 1000.0

    # Hysteresis: only switch exits if the new route is cheaper by this margin (seconds).
    switch_margin_s: float = 5.0


@dataclass
class EdgeObservation:
    """What the vision layer reports for one corridor at one moment."""

    p_fire: float = 0.0
    p_smoke: float = 0.0
    p_block: float = 0.0
    people: float = 0.0  # count of people currently in the corridor


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def walking_speed(rho: float, cfg: RiskConfig) -> float:
    """Weidmann speed-density relation, clamped to [v_min, v_free]."""
    if rho <= 0:
        return cfg.v_free
    if rho >= cfg.rho_max:
        return cfg.v_min
    v = cfg.v_free * (1.0 - math.exp(-cfg.gamma * (1.0 / rho - 1.0 / cfg.rho_max)))
    return min(cfg.v_free, max(cfg.v_min, v))


def hazard_risk(obs: EdgeObservation, cfg: RiskConfig) -> float:
    s = cfg.severity
    q = (
        (1.0 - s["fire"] * _clamp01(obs.p_fire))
        * (1.0 - s["smoke"] * _clamp01(obs.p_smoke))
        * (1.0 - s["blocked"] * _clamp01(obs.p_block))
    )
    return 1.0 - q


def is_blocked(obs: EdgeObservation, cfg: RiskConfig) -> bool:
    return obs.p_fire > cfg.tau_fire or obs.p_block > cfg.tau_block


def dominant_hazard(obs: EdgeObservation | None, cfg: RiskConfig) -> tuple[str, float]:
    """Name and (severity-weighted) probability of the strongest hazard on an edge."""
    if obs is None:
        return "unmonitored area", cfg.unknown_prior_risk
    s = cfg.severity
    cands = {
        "fire": s["fire"] * obs.p_fire,
        "smoke": s["smoke"] * obs.p_smoke,
        "blocked path": s["blocked"] * obs.p_block,
    }
    name = max(cands, key=cands.get)
    return name, cands[name]


@dataclass(frozen=True)
class EdgeCost:
    free_flow_time: float
    crowd_delay: float
    hazard_penalty: float
    risk: float
    density: float
    blocked: bool
    blocked_penalty: float = 0.0

    @property
    def travel_time(self) -> float:
        return self.free_flow_time + self.crowd_delay

    @property
    def total(self) -> float:
        return self.free_flow_time + self.crowd_delay + self.hazard_penalty + self.blocked_penalty


def edge_cost(edge: Edge, obs: EdgeObservation | None, cfg: RiskConfig, relax: bool = False) -> EdgeCost:
    """Cost components for one corridor. `relax=True` prices blocked edges instead of forbidding them."""
    if obs is None:
        # No detections reported. Camera-covered => clear; no camera => unknown-coverage prior.
        risk = cfg.unknown_prior_risk if edge.camera is None else 0.0
        blocked, people = False, 0.0
    else:
        risk = hazard_risk(obs, cfg)
        blocked = is_blocked(obs, cfg)
        people = max(0.0, obs.people)

    rho = people / edge.area
    v = walking_speed(rho, cfg)
    free = edge.length / cfg.v_free
    crowd_delay = edge.length / v - free  # >= 0 because v <= v_free
    return EdgeCost(
        free_flow_time=free,
        crowd_delay=crowd_delay,
        hazard_penalty=cfg.lam * risk,
        risk=risk,
        density=rho,
        blocked=blocked,
        blocked_penalty=cfg.blocked_penalty_s if (blocked and relax) else 0.0,
    )
