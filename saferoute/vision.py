"""Computer-vision layer: turns camera frames into the same EdgeObservation the
planner already consumes (Steps 1-2 used mocked/simulated observations).

Design:
  * `Detector` is a small protocol so the aggregation and camera-source logic can be
    tested with a fake detector, with no torch/ultralytics dependency in tests.
  * `YoloFireSmokeDetector` / `YoloPersonDetector` wrap Ultralytics YOLO and lazy-import
    it, so importing this module never requires ultralytics to be installed.
  * `CorridorObserver` runs one or more detectors on frames from one camera, and turns
    a short rolling window of per-frame detections into ONE EdgeObservation via an
    exponential moving average (temporal smoothing -> fewer one-frame false alarms).
  * `VisionPerception` mirrors saferoute.perception.Perception's interface
    (advance_to / observations), so `RoutePlanner` and `scripts/run_scenario.py`-style
    code work unchanged whether observations come from the simulator or from real video.

Class name conventions (must match the trained model's names, see saferoute/vision_config.py):
  fire/smoke model: "fire", "smoke"
  person model:     "person" (COCO class 0, pretrained yolov8n.pt already has it)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .risk import EdgeObservation


@dataclass
class Detection:
    cls: str
    conf: float
    xyxy: tuple[float, float, float, float]


@dataclass
class FrameDetections:
    detections: list[Detection] = field(default_factory=list)
    frame_time: float = 0.0
    infer_ms: float = 0.0

    def confidences(self, cls: str) -> list[float]:
        return [d.conf for d in self.detections if d.cls == cls]

    def max_conf(self, cls: str) -> float:
        cs = self.confidences(cls)
        return max(cs) if cs else 0.0

    def count(self, cls: str) -> int:
        return len(self.confidences(cls))


class Detector(Protocol):
    """Anything with this method can be used in place of a real YOLO model (see tests)."""

    def detect(self, frame) -> FrameDetections: ...


class YoloDetector:
    """Thin wrapper around ultralytics.YOLO. Lazy-imports ultralytics so this module
    loads fine without it (only object construction / .detect() need it installed)."""

    def __init__(self, weights: str | Path, conf: float = 0.25, classes: list[str] | None = None):
        self.weights = str(weights)
        self.conf = conf
        self.classes = classes  # restrict to these class names if given
        self._model = None

    def _load(self):
        if self._model is None:
            from ultralytics import YOLO  # noqa: local import, heavy dependency

            self._model = YOLO(self.weights)
        return self._model

    def detect(self, frame) -> FrameDetections:
        model = self._load()
        t0 = time.perf_counter()
        result = model.predict(frame, conf=self.conf, verbose=False)[0]
        infer_ms = (time.perf_counter() - t0) * 1000.0
        names = result.names
        dets = []
        for box in result.boxes:
            name = names[int(box.cls[0])]
            if self.classes and name not in self.classes:
                continue
            dets.append(Detection(cls=name, conf=float(box.conf[0]), xyxy=tuple(box.xyxy[0].tolist())))
        return FrameDetections(detections=dets, frame_time=time.time(), infer_ms=infer_ms)


def YoloFireSmokeDetector(weights: str | Path, conf: float = 0.25) -> YoloDetector:
    """Fine-tuned on D-Fire (Step 3 training). Class names must be 'fire' and 'smoke'."""
    return YoloDetector(weights, conf=conf, classes=["fire", "smoke"])


def YoloPersonDetector(weights: str | Path = "yolov8n.pt", conf: float = 0.35) -> YoloDetector:
    """COCO-pretrained; no fine-tuning needed. Ultralytics auto-downloads yolov8n.pt if missing."""
    return YoloDetector(weights, conf=conf, classes=["person"])


@dataclass
class ObserverConfig:
    ema_alpha: float = 0.4  # temporal smoothing across frames (matches perception.PerceptionConfig)
    person_area_m2: float = 20.0  # approx floor area a person's box represents, for a rough density proxy
    reference_frame_area: float = 1_000_000.0  # a nominal frame's box-area units (calibrate per camera/lens)
    fps_limit: float = 4.0  # run detectors at most this often (real-time CPU inference budget)


class CorridorObserver:
    """One camera, mapped to one corridor edge. Runs the fire/smoke and person detectors
    on incoming frames and maintains a smoothed EdgeObservation."""

    def __init__(self, edge_id: str, fire_smoke: Detector | None, person: Detector | None, cfg: ObserverConfig | None = None):
        self.edge_id = edge_id
        self.fire_smoke = fire_smoke
        self.person = person
        self.cfg = cfg or ObserverConfig()
        self._fire = 0.0
        self._smoke = 0.0
        self._people = 0.0
        self._last_t = -1e18
        self.last_detections: FrameDetections | None = None
        self.last_infer_ms = 0.0

    def update(self, frame, t: float) -> None:
        """Feed one frame. Cheap no-op if called faster than fps_limit."""
        min_dt = 1.0 / self.cfg.fps_limit
        if t - self._last_t < min_dt:
            return
        self._last_t = t
        a = self.cfg.ema_alpha

        if self.fire_smoke is not None:
            fd = self.fire_smoke.detect(frame)
            self.last_detections, self.last_infer_ms = fd, fd.infer_ms
            self._fire = a * fd.max_conf("fire") + (1 - a) * self._fire
            self._smoke = a * fd.max_conf("smoke") + (1 - a) * self._smoke

        if self.person is not None:
            pd = self.person.detect(frame)
            self._people = a * pd.count("person") + (1 - a) * self._people

    def observation(self) -> EdgeObservation:
        return EdgeObservation(p_fire=self._fire, p_smoke=self._smoke, p_block=0.0, people=self._people)


class VisionPerception:
    """Same interface as saferoute.perception.Perception, backed by real (or file) cameras
    instead of the ground-truth simulator. Corridors with no camera simply have no observer,
    so RoutePlanner falls back to the unknown-coverage prior for them (see risk.py)."""

    def __init__(self, observers: dict[str, CorridorObserver]):
        self.observers = observers  # edge_id -> CorridorObserver

    def advance_to(self, t: float) -> None:
        """No-op: real cameras push frames via feed_frame(); nothing to precompute here."""

    def feed_frame(self, edge_id: str, frame, t: float) -> None:
        obs = self.observers.get(edge_id)
        if obs is not None:
            obs.update(frame, t)

    def observations(self) -> dict[str, EdgeObservation]:
        return {eid: o.observation() for eid, o in self.observers.items()}
