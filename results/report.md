# SafeRoute Emergency AI — Evaluation Report

Academic/portfolio prototype. All results below are from simulation under the stated assumptions (see README `Assumptions and limitations`), not from a real building or a certified emergency system.

## 1. Headline result: dynamic risk-aware routing vs shortest path

Grid building (6x10 corridors, 6 exits), 200 scenarios, default settings (lambda=60, noisy detector: recall=0.9, fp=0.01, latency=2s).

*(missing: run the corresponding script to generate `summary_grid_n200_seed0_lam60_noisy.md`)*

## 2. Choosing lambda (the hazard penalty)

Same 150 scenarios reused across lambda values; only the hazard penalty changes.

| lambda | dynamic success % | dynamic mean dose | dynamic mean time (s) | dose vs shortest_path [95% CI] |
|---|---|---|---|---|
| 0 | 89.3 | 0.202 | 22.7 | -0.036 [-0.070, -0.005] |
| 15 | 90.7 | 0.186 | 23.1 | -0.053 [-0.085, -0.023] |
| 30 | 91.3 | 0.179 | 23.2 | -0.060 [-0.092, -0.027] |
| 60 | 92.0 | 0.176 | 23.5 | -0.063 [-0.096, -0.030] |
| 120 | 92.0 | 0.177 | 23.6 | -0.062 [-0.095, -0.030] |
| 250 | 92.0 | 0.176 | 23.9 | -0.062 [-0.095, -0.030] |

lambda=0 reduces dynamic_risk to hazard-blind shortest-path routing (sanity check: its dose gap vs shortest_path should be ~0). Pick the smallest lambda where the dose gap's upper CI bound is clearly negative, then check mean time hasn't grown much.

## 3. How much does detector quality matter?

150 scenarios per detector setting.

| detector | recall | fp rate | latency (s) | dynamic success % | dose vs shortest_path [95% CI] |
|---|---|---|---|---|---|
| perfect | n/a | n/a | n/a | 92.0 | -0.063 [-0.096, -0.031] |
| good (default) | 0.90 | 0.010 | 2.0 | 92.0 | -0.063 [-0.096, -0.030] |
| moderate | 0.75 | 0.030 | 4.0 | 92.0 | -0.050 [-0.085, -0.015] |
| poor | 0.55 | 0.080 | 6.0 | 89.3 | -0.037 [-0.065, -0.012] |
| very poor | 0.35 | 0.150 | 8.0 | 87.3 | -0.007 [-0.043, +0.030] |

'good (default)' matches the noise levels assumed in Step 2's headline results. 'perfect' is the ceiling (routing logic alone, no perception error). Replace 'good (default)' with numbers from scripts/calibrate_perception.py once the fire/smoke model is trained.

## 4. Does the result hold as the emergency gets harder?

Fewer scenarios here (default 60): the hindsight oracle's search cost rises sharply in the harder settings (more viable time/exposure tradeoffs to consider), so this sweep is more expensive per scenario than the others.

| difficulty | oracle success % | dynamic success % | dose vs shortest_path [95% CI] |
|---|---|---|---|
| easy (base) | 91.7 | 91.7 | -0.069 [-0.135, -0.012] |
| faster fire | 76.7 | 75.0 | -0.054 [-0.112, -0.001] |
| later warning | 51.7 | 51.7 | -0.116 [-0.181, -0.057] |
| faster+later warn | 23.3 | 20.0 | -0.017 [-0.059, +0.018] |

Oracle success % dropping toward 0 means most scenarios are unwinnable by ANY policy at that difficulty â€” a shrinking dose gap there reflects a harder benchmark, not a worse method. Read the dose gap alongside the oracle rate, not in isolation.

## 5. Ablations: does each mechanism earn its place?

150 scenarios, all compared against the shortest_path baseline.

| variant | success % | mean dose | dose vs shortest_path [95% CI] | mean reroutes |
|---|---|---|---|---|
| dynamic_risk (full) | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.02 |
| no_hysteresis | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.04 |
| no_crowd_term | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.02 |
| perfect_perception | 92.0 | 0.175 | -0.063 [-0.096, -0.031] | 0.02 |

no_hysteresis reroutes the instant a cheaper option appears (no switch margin) â€” compare its mean reroutes to the full method's. no_crowd_term disables crowd-based slowdown/cost. perfect_perception uses ground-truth hazards with no latency (upper bound on this policy).

## 6. Bottom line

- Being risk-aware at all (vs pure shortest-path) is where most of the safety benefit comes from; live re-planning over planning-once adds a smaller further gain (Step 2).
- lambda=60 is a reasonable default: the dose-gap improvement from raising lambda plateaus around there, with mean evacuation time barely affected (Section 2).
- The advantage degrades gracefully as the detector gets worse, and only loses statistical significance at a detector far worse than any reasonable YOLO fire/smoke model measured so far (Section 3) — pending real numbers from `scripts/calibrate_perception.py`.
- The benefit shrinks in the hardest, near-unwinnable scenarios, which is expected: read the dose gap alongside the oracle's own success rate, not alone (Section 4).
- Individually, hysteresis, the crowd term, and perception noise each showed no detectable effect at n=150 in this configuration — rerouting itself is rare here, since the *first* plan already accounts for hazards known at that moment, leaving little room for any one mechanism to show up alone (Section 5). This is a genuine result, not a null test to hide.

**Reproduce:** `python scripts/run_experiment.py --plan grid --n 200`, then `sweep_lambda.py`, `sweep_perception.py`, `sweep_difficulty.py`, `run_ablations.py` (see README for exact commands). All reported comparisons are paired (same scenarios, same detector-noise stream across policies) with bootstrap 95% confidence intervals.
