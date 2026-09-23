"""Perception layer: what the routing system *believes* about each camera-covered corridor.

`mode="perfect"` reports the ground truth (upper bound). `mode="noisy"` emulates a detector:
per-frame recall, false alarms, latency, and EMA temporal smoothing. Step 3 replaces this with
real YOLO detections and calibrates these parameters from measured precision/recall.

Determinism: the RNG is consumed once per (second, edge) tick in a fixed order, so two policies
using the same seed see the same detector noise wherever their timelines overlap (paired comparison).
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from .graph import BuildingGraph
from .risk import EdgeObservation
from .scenario import Scenario


@dataclass
class PerceptionConfig:
    mode: str = "noisy"  # "noisy" | "perfect"
    recall: float = 0.90  # per-second probability a real fire is detected (also smoke unless recall_smoke is set)
    recall_smoke: float | None = None
    recall_obstacle: float = 0.70
    fp_rate: float = 0.01  # per-second probability of a false alarm on a clear corridor (fire; smoke unless overridden)
    fp_rate_smoke: float | None = None
    latency_s: float = 2.0  # detections describe the world this many seconds ago
    ema_alpha: float = 0.5  # temporal smoothing (1.0 = no smoothing)
    count_noise_rel: float = 0.15  # relative std-dev of people-count error
    warmup_s: int = 10  # seconds of history processed before t=0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PerceptionConfig":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})

    @classmethod
    def from_json(cls, path: str | Path) -> "PerceptionConfig":
        return cls.from_dict(json.loads(Path(path).read_text()))


    @classmethod
    def from_json(cls, path: str | Path) -> "PerceptionConfig":
        """Load values measured by scripts/evaluate_detector.py (unknown keys such as `details` are ignored)."""
        d = json.loads(Path(path).read_text())
        known = {f.name for f in fields(cls)} - {"mode"}
        return cls(**{k: v for k, v in d.items() if k in known and v is not None})


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


class Perception:
    def __init__(self, graph: BuildingGraph, scenario: Scenario, cfg: PerceptionConfig, rng: random.Random):
        self.graph, self.scn, self.cfg, self.rng = graph, scenario, cfg, rng
        self.t_next = -cfg.warmup_s
        self._state: dict[str, list[float]] = {eid: [0.0, 0.0, 0.0] for eid, e in graph.edges.items() if e.camera}
        self._people: dict[str, float] = {eid: 0.0 for eid in self._state}

    def advance_to(self, t: float) -> None:
        while self.t_next <= t:
            self._tick(self.t_next)
            self.t_next += 1

    def _tick(self, t: int) -> None:
        c, r = self.cfg, self.rng
        ts = t - c.latency_s
        for eid in self._state:  # insertion order is fixed => deterministic RNG use
            fire, smoke = self.scn.fire_on(eid, ts), self.scn.smoke_level(eid, ts)
            block, n = self.scn.blocked(eid, ts), self.scn.people(eid, ts)
            st = self._state[eid]
            if c.mode == "perfect":
                st[0], st[1], st[2] = float(fire), smoke, float(block)
                self._people[eid] = n
                continue
            raw_f = self._binary(fire, c.recall)
            raw_b = self._binary(block, c.recall_obstacle)
            raw_s = self._smoke(smoke)
            a = c.ema_alpha
            st[0] = a * raw_f + (1 - a) * st[0]
            st[1] = a * raw_s + (1 - a) * st[1]
            st[2] = a * raw_b + (1 - a) * st[2]
            self._people[eid] = max(0.0, n * (1.0 + r.gauss(0.0, c.count_noise_rel)))

    def _binary(self, truth: bool, recall: float) -> float:
        r = self.rng
        if truth:
            return r.uniform(0.7, 0.98) if r.random() < recall else r.uniform(0.0, 0.3)
        return r.uniform(0.6, 0.9) if r.random() < self.cfg.fp_rate else r.uniform(0.0, 0.1)

    def _smoke(self, level: float) -> float:
        r, c = self.rng, self.cfg
        recall = c.recall if c.recall_smoke is None else c.recall_smoke
        fp = c.fp_rate if c.fp_rate_smoke is None else c.fp_rate_smoke
        if level > 0.05:
            if r.random() < recall:
                return _clip01(level * r.uniform(0.8, 1.1) + r.gauss(0.0, 0.05))
            return r.uniform(0.0, 0.1)
        return r.uniform(0.4, 0.8) if r.random() < fp else r.uniform(0.0, 0.05)

    def observations(self) -> dict[str, EdgeObservation]:
        return {
            eid: EdgeObservation(p_fire=st[0], p_smoke=st[1], p_block=st[2], people=self._people[eid])
            for eid, st in self._state.items()
        }
