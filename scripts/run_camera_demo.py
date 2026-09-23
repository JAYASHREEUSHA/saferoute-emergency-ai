"""Live version of scripts/run_scenario.py: hazards come from real cameras/video instead of a
scripted timeline. Requires: pip install ultralytics opencv-python (see requirements.txt).

Usage:
  python scripts/run_camera_demo.py                            # use data/camera_config.json as-is
  python scripts/run_camera_demo.py --user-at C1                # start the simulated user elsewhere
  python scripts/run_camera_demo.py --camera cam_A1=0            # override one corridor with webcam 0
  python scripts/run_camera_demo.py --no-display                 # headless (e.g. over SSH)

Notes:
  * User position is still simulated; pass --user-at to change it. See README Step 3
    limitations on why GPS/indoor localization is out of scope for this prototype.
  * If runs/fire_smoke/weights/best.pt does not exist yet (no fine-tuned model), fire/smoke
    detection is skipped and only person counts are shown, so the demo still runs end to end.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from saferoute import BuildingGraph, RiskConfig, RoutePlanner, explain  # noqa: E402
from saferoute.camera import CameraSource, MultiCameraRig  # noqa: E402
from saferoute.vision import CorridorObserver, VisionPerception, YoloFireSmokeDetector, YoloPersonDetector  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config", default=str(ROOT / "data" / "camera_config.json"))
ap.add_argument("--plan", default=str(ROOT / "data" / "floorplan_mall.json"))
ap.add_argument("--user-at", default="S")
ap.add_argument("--camera", action="append", default=[], help="override, e.g. cam_A1=0")
ap.add_argument("--no-display", action="store_true")
ap.add_argument("--seconds", type=float, default=None, help="stop after this many seconds (for scripted runs)")
a = ap.parse_args()

cfg = json.loads(Path(a.config).read_text())
for ov in a.camera:
    k, v = ov.split("=", 1)
    cfg["cameras"][k] = int(v) if v.lstrip("-").isdigit() else v

graph = BuildingGraph.from_json(a.plan)
risk_cfg = RiskConfig()
planner = RoutePlanner(graph, risk_cfg)

fs_weights = ROOT / cfg["fire_smoke_weights"]
fire_smoke_detector = YoloFireSmokeDetector(fs_weights) if fs_weights.exists() else None
if fire_smoke_detector is None:
    print(f"[warn] no fire/smoke weights at {fs_weights} — run scripts/train_fire_smoke.py first "
          f"(see notebooks/train_fire_smoke_colab.ipynb for a GPU-backed version).\n"
          f"        Continuing with person detection only.\n")
person_detector = YoloPersonDetector(cfg["person_weights"])

edge_cams = {e.camera: e.id for e in graph.edges.values() if e.camera}
observers, sources = {}, []
for cam_id, source in cfg["cameras"].items():
    edge_id = edge_cams.get(cam_id)
    if edge_id is None:
        continue
    observers[edge_id] = CorridorObserver(edge_id, fire_smoke_detector, person_detector)
    sources.append(CameraSource(edge_id=edge_id, source=source, label=cam_id))

if not sources:
    raise SystemExit("No cameras in the config match a corridor in the floor plan. Check data/camera_config.json.")

perception = VisionPerception(observers)

try:
    import cv2
except ImportError:
    cv2 = None
    a.no_display = True

print(f"Watching {len(sources)} corridor(s): {', '.join(s.label for s in sources)}")
print("Press Ctrl+C to stop.\n")

t0 = time.time()
last_print = 0.0
with MultiCameraRig(sources, perception) as rig:
    try:
        while True:
            t = time.time() - t0
            if a.seconds is not None and t > a.seconds:
                break
            frames = rig.step(t)

            if t - last_print > 2.0:  # don't spam the terminal every frame
                last_print = t
                decision = planner.update(perception.observations(), a.user_at)
                ex = explain(decision, graph, perception.observations(), risk_cfg)
                print(f"[t={t:5.1f}s] {ex.headline}")
                for row in ex.table:
                    star = "*" if row["recommended"] else " "
                    print(f"    {row['exit']:8} {row['status']:9} risk={row['route_risk']} {star}")

            if not a.no_display and cv2 is not None:
                for edge_id, frame in frames.items():
                    if frame is not None:
                        cv2.imshow(edge_id, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass

if not a.no_display and cv2 is not None:
    cv2.destroyAllWindows()
