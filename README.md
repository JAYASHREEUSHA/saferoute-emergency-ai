# SafeRoute Emergency AI

Risk-aware, explainable evacuation routing prototype. Computer-vision hazard detections (Step 3+)
update a building risk graph; a planner recommends the lowest-risk exit and explains why.
Evaluated in simulation against shortest-path routing.

> **Academic/portfolio prototype. Not a certified or real-world emergency system.**
> All results are from simulation under stated assumptions. Always follow official alarms,
> signage and staff instructions.

## Status

| Step | Content | State |
|---|---|---|
| 1 | Graph, risk model, A*, hysteresis, explanations, scripted scenario, tests | done |
| 2 | Simulator (fire/smoke spread, crowds, dose), baselines, hindsight oracle, Monte Carlo evaluation | done |
| 3 | YOLOv8n fire/smoke/person detection, camera-to-corridor bridge, training pipeline, calibration | done |
| 4 | FastAPI + WebSocket, SQLite event log | next |
| 5 | React dashboard, voice, scripted demo | |
| 6 | Sensitivity experiments (lambda sweep, detector noise, difficulty), report, demo video | |

## Quick start (Windows PowerShell, from the `saferoute` folder)

```powershell
python -m pip install -r requirements.txt
python scripts\run_scenario.py                                  # Step 1 demo: A -> B -> C -> B with explanations
python -m pytest -q                                             # 29 tests
python scripts\run_experiment.py --plan grid --n 200            # Step 2 experiment (~90 s), writes results\
python scripts\run_experiment.py --plan mall --n 200
python scripts\run_experiment.py --plan grid --n 200 --lam 30   # try a different hazard penalty
python scripts\run_experiment.py --plan grid --n 200 --recall 0.7 --fp 0.05 --latency 4   # worse detector

# Step 3 (computer vision) — optional, needs pip install ultralytics opencv-python:
python -m pytest tests\test_vision.py -q                        # aggregation logic, no ultralytics needed
python scripts\run_camera_demo.py --camera cam_A1=0              # webcam 0 as Corridor A (inner); Ctrl+C to stop
python scripts\calibrate_perception.py                            # after training, measures real recall/fp/latency
```

## Layout

```
data/floorplan_mall.json     3-exit demo building
saferoute/graph.py           BuildingGraph, JSON loading, validation
saferoute/buildings.py       grid_building(): corridor-lattice generator for experiments
saferoute/risk.py            crowd speed model, hazard risk, edge cost
saferoute/planner.py         A*, per-exit evaluation, RoutePlanner with hysteresis, best_route
saferoute/explain.py         explanations + dashboard table from the real cost breakdown
saferoute/scenario.py        ground-truth world: fire/smoke spread, crowd hotspots, obstacles
saferoute/perception.py      what the router believes: recall, false alarms, latency, EMA smoothing
saferoute/sim.py             agent movement, crowd/smoke slowdown, dose accumulation, outcome metrics
saferoute/policies.py        shortest_path, static_risk, dynamic_risk (proposed)
saferoute/oracle.py          hindsight-optimal route (exact, upper bound)
saferoute/experiment.py      paired Monte Carlo runner, bootstrap CIs, summary tables
saferoute/vision.py          Detector protocol, YOLO wrapper, CorridorObserver, VisionPerception
saferoute/camera.py          OpenCV camera/video sources -> VisionPerception
data/camera_config.json      camera id -> video source mapping (fill in real paths/webcam indices)
training/                    dfire.yaml, train_fire_smoke.py, README (dataset + training instructions)
notebooks/train_fire_smoke_colab.ipynb   GPU training notebook (Colab-ready)
eval/README.md               held-out test-set format for scripts/calibrate_perception.py
scripts/run_scenario.py      Step 1 scripted demo
scripts/run_experiment.py    Step 2 experiment CLI
scripts/run_camera_demo.py   Step 3 live demo: camera/video -> detections -> route
scripts/calibrate_perception.py   measures real detector recall/fp-rate/latency
results/                     example output (CSV per run + markdown summary)
tests/                       test_step1.py, test_step2.py, test_vision.py
```

## Risk model (Step 1)

Time is the common currency (seconds-equivalent), so there are few arbitrary weights.

```
t_e  = L_e / v(rho_e)                          crowd -> travel time (Weidmann speed-density)
r_e  = 1 - (1 - s_f p_fire)(1 - s_s p_smoke)(1 - s_b p_block)
c_e  = t_e + lambda * r_e                      edge cost
R    = 1 - prod(1 - r_e)                       route risk (reported to the user)
```

`lambda` = seconds of delay accepted to avoid a certain hazard (default 60, NOT yet tuned). Fire or a blocked
corridor above a threshold is impassable. Unmonitored corridors get a prior risk. Hysteresis stops route
flip-flopping. If every exit is blocked, the least-bad route is returned with a warning. Explanations are
generated from the cost components, so they cannot disagree with the decision.

## Simulation and evaluation (Step 2)

**World.** One evacuee walks a corridor graph. A fire ignites at a junction near the user (before the alarm),
spreads along corridors at a constant speed; smoke travels faster and ramps up; crowd hotspots appear; an obstacle
may block a corridor. Every hazard only gets worse over time (monotone), which makes the oracle exact.
People never step into a corridor that is visibly on fire or blocked (applies to ALL policies, so the
baseline is not a strawman). Smoke and crowds slow walking. A dose counter accumulates in smoke and flames
(a simplified incapacitation proxy, not a validated toxicity model); dose >= 1 means the evacuee is incapacitated.

**Policies compared** (same scenarios, same detector-noise stream => paired comparison):

| Policy | What it does |
|---|---|
| `shortest_path` | nearest exit by distance, ignores hazards except visible fire/obstacles |
| `static_risk` | risk-aware route planned once from the t=0 observations, then followed |
| `dynamic_risk` | **proposed**: re-plans at every junction from live (noisy, delayed, smoothed) detections, with hysteresis |
| `dynamic_perfect_perception` | same planner, ground-truth hazards, no latency (perception upper bound) |
| `oracle` | knows the whole future; exact best route (upper bound, not deployable) |

**Metrics:** escape success, final dose, evacuation time (successful runs), time in smoke, time in flames,
reroute count, planning latency; paired bootstrap 95% CIs; regret vs oracle.

### Example results (grid 6x10, 200 scenarios, seed 0, lambda=60, noisy detector)

| Policy | Success % | Mean dose | Dose, hazard-relevant scenarios (81/200) |
|---|---|---|---|
| shortest_path | 87.5 | 0.213 | 0.518 |
| static_risk | 92.5 | 0.163 | 0.379 |
| dynamic_risk | 94.0 | 0.153 | 0.359 |
| dynamic_perfect_perception | 94.0 | 0.150 | 0.355 |
| oracle | 94.0 | 0.133 | 0.322 |

Paired vs shortest path: dynamic_risk dose -0.060 [-0.086, -0.034], success +6.5 pp [+3.5, +10.0]. In hazard-relevant
scenarios: dose -0.159 [-0.223, -0.101], success +16.0 pp [+8.6, +24.7]. Live re-planning vs planning once: a small gain
(dose -0.010 [-0.019, -0.002]). Regret vs oracle: 0.021 [0.011, 0.033]. Full tables in `results/`.

**Honest reading.** Most of the benefit comes from being risk-aware at all; live re-planning adds a small extra gain
in this simulator. On the tiny 3-exit mall the noisy `dynamic_risk` was NOT significantly better than shortest path
(CIs include zero), because there are few alternative routes. Do not generalise beyond the tested conditions.

## Computer vision (Step 3)

`saferoute/vision.py` turns YOLO detections into the SAME `EdgeObservation` the planner
already consumes, so `RoutePlanner` and `explain()` need no changes to run on real cameras.

- **`CorridorObserver`**: one camera bound to one corridor edge. Runs a fire/smoke detector
  and a person detector on incoming frames, EMA-smooths their outputs (same idea as the
  `PerceptionConfig` smoothing used in the simulator), and exposes an `EdgeObservation`.
- **`VisionPerception`**: same `.observations()` interface as `saferoute.perception.Perception`,
  backed by real cameras instead of ground truth. Corridors with no camera get no observer,
  so the risk model's unknown-coverage prior applies automatically — consistent with Step 1/2.
- **`saferoute/camera.py`**: OpenCV video/webcam sources, one per corridor (`data/camera_config.json`).
- Fire/smoke uses a YOLOv8n fine-tuned on D-Fire (`training/`, `notebooks/train_fire_smoke_colab.ipynb` —
  train on a GPU, not a laptop CPU). Person detection uses COCO-pretrained `yolov8n.pt`, no
  fine-tuning needed.
- **`scripts/calibrate_perception.py`** measures real recall, false-positive rate and latency
  on a held-out labeled set (`eval/README.md`), so Step 2's assumed detector noise
  (recall=0.9, fp=0.01, latency=2s) can be replaced with measured numbers before reporting
  any evaluation result as final.
- `tests/test_vision.py` covers the aggregation logic (EMA smoothing, fps throttling, class
  filtering) with a fake detector — no ultralytics/torch install needed to run it.

**Not yet done:** the fire/smoke model has not actually been trained (no dataset is bundled —
see `training/README.md` for how to get D-Fire), so `run_camera_demo.py` currently falls back
to person-detection-only if `runs/fire_smoke/weights/best.pt` is missing. Training and
calibration are the two things to run next, on a machine with a GPU and/or a webcam.


- Single evacuee, decisions at junctions only (no mid-corridor U-turns), no crowd-agent interaction or panic behaviour.
- Fire spread, smoke, crowds and dose are simple models with assumed constants; they are not validated against fire
  dynamics software or experiments. Sensitivity checks come in Step 6.
- Scenario difficulty was set by one criterion fixed before comparing policies (oracle escapes in about 90% of
  scenarios on the grid). On the small mall the oracle escapes only about 76%, so many scenarios are unwinnable.
- Detector noise (recall, false alarms, latency) is ASSUMED here; Step 3 measures it from real YOLO outputs.
- The world uses the same crowd-slowdown model as the planner (no model mismatch for crowds). Smoke slowdown is in the
  world but not in the planner's cost.
- The planner reacts to the current hazard and does not predict its spread (Phase 2: hazard-spread forecasting;
  this is the main source of the remaining gap to the oracle).
- User position is a graph node (simulated). GPS is unreliable indoors; not claimed.
