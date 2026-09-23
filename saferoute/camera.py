"""OpenCV camera/video sources for CorridorObserver.

Each source is a video file or a webcam index mapped to one corridor edge. Reading
frames and hazard detection are decoupled from wall-clock time so recorded video can
be replayed at its own timestamps (needed for the D-Fire-style clips used in demos).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import cv2

from .vision import CorridorObserver, VisionPerception


@dataclass
class CameraSource:
    edge_id: str
    source: str | int  # file path or webcam index (0, 1, ...)
    label: str = ""

    def open(self) -> "cv2.VideoCapture":
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"could not open camera/video source: {self.source!r} (corridor {self.edge_id})")
        return cap


class MultiCameraRig:
    """Reads one frame at a time from every configured source and feeds VisionPerception.
    Designed for the demo script; a production system would run one thread/process per camera."""

    def __init__(self, sources: list[CameraSource], perception: VisionPerception):
        self.sources = sources
        self.perception = perception
        self._caps: dict[str, cv2.VideoCapture] = {}

    def open(self) -> None:
        self._caps = {s.edge_id: s.open() for s in self.sources}

    def close(self) -> None:
        for cap in self._caps.values():
            cap.release()
        self._caps = {}

    def step(self, t: float) -> dict[str, "cv2.typing.MatLike | None"]:
        """Read one frame from every source, feed detectors, return the frames (for display)."""
        frames = {}
        for s in self.sources:
            cap = self._caps[s.edge_id]
            ok, frame = cap.read()
            if not ok:  # loop finite clips so a short demo video can run indefinitely
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
            frames[s.edge_id] = frame if ok else None
            if ok:
                self.perception.feed_frame(s.edge_id, frame, t)
        return frames

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()
