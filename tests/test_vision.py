from saferoute.vision import CorridorObserver, Detection, FrameDetections, ObserverConfig, VisionPerception


class FakeDetector:
    """Deterministic stand-in for YoloDetector: returns a scripted detection per call."""

    def __init__(self, script: list[list[Detection]]):
        self.script = script
        self.i = 0

    def detect(self, frame) -> FrameDetections:
        dets = self.script[min(self.i, len(self.script) - 1)]
        self.i += 1
        return FrameDetections(detections=dets, frame_time=0.0, infer_ms=1.0)


def test_no_detections_gives_zero_observation():
    obs = CorridorObserver("e1", FakeDetector([[]]), FakeDetector([[]]))
    obs.update(frame=None, t=0.0)
    o = obs.observation()
    assert o.p_fire == 0.0 and o.p_smoke == 0.0 and o.people == 0.0


def test_fire_detection_raises_p_fire_with_smoothing():
    script = [[Detection("fire", 0.9, (0, 0, 1, 1))]] * 5
    obs = CorridorObserver("e1", FakeDetector(script), None, ObserverConfig(ema_alpha=0.5, fps_limit=1000))
    vals = []
    for i in range(5):
        obs.update(frame=None, t=i * 1.0)
        vals.append(obs.observation().p_fire)
    assert all(b >= a - 1e-9 for a, b in zip(vals, vals[1:]))  # EMA rises monotonically toward 0.9
    assert vals[-1] > 0.9 * 0.9  # nearly converged after 5 steps at alpha=0.5


def test_fps_limit_throttles_updates():
    script = [[Detection("fire", 1.0, (0, 0, 1, 1))]] * 10
    obs = CorridorObserver("e1", FakeDetector(script), None, ObserverConfig(ema_alpha=1.0, fps_limit=1.0))
    obs.update(frame=None, t=0.0)
    obs.update(frame=None, t=0.1)  # too soon, ignored
    assert obs.observation().p_fire == 1.0
    assert obs.fire_smoke.i == 1  # detector called only once


def test_person_count_feeds_people_field():
    dets = [Detection("person", 0.8, (0, 0, 1, 1)), Detection("person", 0.7, (2, 2, 3, 3))]
    obs = CorridorObserver("e1", None, FakeDetector([dets]), ObserverConfig(ema_alpha=1.0))
    obs.update(frame=None, t=0.0)
    assert obs.observation().people == 2


def test_unrelated_classes_are_ignored():
    dets = [Detection("chair", 0.99, (0, 0, 1, 1))]
    obs = CorridorObserver("e1", FakeDetector([dets]), None, ObserverConfig(ema_alpha=1.0))
    obs.update(frame=None, t=0.0)
    o = obs.observation()
    assert o.p_fire == 0.0 and o.p_smoke == 0.0


def test_vision_perception_matches_dict_interface():
    a = CorridorObserver("e1", FakeDetector([[Detection("smoke", 0.6, (0, 0, 1, 1))]]), None, ObserverConfig(ema_alpha=1.0))
    a.update(frame=None, t=0.0)
    vp = VisionPerception({"e1": a})
    vp.advance_to(0.0)  # no-op, but must not raise
    obs = vp.observations()
    assert set(obs) == {"e1"}
    assert obs["e1"].p_smoke == 0.6


def test_no_camera_edge_absent_from_observations():
    vp = VisionPerception({})
    assert vp.observations() == {}
