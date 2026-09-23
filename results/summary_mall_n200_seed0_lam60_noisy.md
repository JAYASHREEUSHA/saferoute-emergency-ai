# Demo mall (3 exits) | lambda=60 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 72.5 [66.5, 78.5] | 0.357 [0.295, 0.417] | 16.4 / 28.9 | 29.3 | 0.9 | 0.02 | 0.045 |
| static_risk | 74.5 [68.5, 80.5] | 0.333 [0.272, 0.391] | 16.7 / 28.4 | 28.2 | 0.7 | 0.00 | 0.432 |
| dynamic_risk | 74.5 [68.5, 80.5] | 0.333 [0.272, 0.391] | 16.7 / 28.4 | 28.2 | 0.7 | 0.00 | 0.349 |
| dynamic_perfect_perception | 76.0 [70.0, 82.0] | 0.317 [0.258, 0.375] | 16.8 / 28.4 | 27.8 | 0.6 | 0.00 | 0.321 |
| oracle | 76.5 [70.5, 82.5] | 0.312 [0.253, 0.369] | 16.9 / 28.7 | 4.3 | 0.3 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +2.0 [-1.0, +5.5] | -0.024 [-0.056, +0.005] | +0.1 [-0.2, +0.4] |
| dynamic_risk | +2.0 [-1.0, +5.5] | -0.024 [-0.056, +0.005] | +0.1 [-0.2, +0.4] |
| dynamic_perfect_perception | +3.5 [+1.0, +6.5] | -0.040 [-0.070, -0.014] | -0.1 [-0.4, +0.2] |
| oracle | +4.0 [+1.5, +7.0] | -0.045 [-0.075, -0.021] | -0.1 [-0.4, +0.2] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +0.0 [+0.0, +0.0] | +0.000 [+0.000, +0.000] | +0.0 [+0.0, +0.0] |
| dynamic_perfect_perception | +1.5 [+0.0, +3.5] | -0.016 [-0.031, -0.004] | -0.2 [-0.4, -0.1] |

## Hazard-relevant scenarios (113 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 51.3 [41.6, 61.1] | 0.627 [0.556, 0.702] | 20.4 / 32.7 | 51.7 | 1.5 | 0.04 | 0.025 |
| static_risk | 55.8 [46.0, 65.5] | 0.574 [0.495, 0.649] | 20.7 / 32.2 | 49.7 | 1.2 | 0.00 | 0.426 |
| dynamic_risk | 55.8 [46.0, 65.5] | 0.574 [0.495, 0.649] | 20.7 / 32.2 | 49.7 | 1.2 | 0.00 | 0.343 |
| dynamic_perfect_perception | 57.5 [47.8, 67.3] | 0.557 [0.478, 0.632] | 20.8 / 33.6 | 49.1 | 1.1 | 0.00 | 0.409 |
| oracle | 58.4 [48.7, 68.1] | 0.547 [0.469, 0.623] | 20.7 / 30.9 | 7.6 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +4.4 [-0.9, +10.6] | -0.054 [-0.110, -0.005] | -0.0 [-0.8, +0.7] |
| dynamic_risk | +4.4 [-0.9, +10.6] | -0.054 [-0.110, -0.005] | -0.0 [-0.8, +0.7] |
| dynamic_perfect_perception | +6.2 [+0.9, +11.5] | -0.071 [-0.126, -0.024] | -0.3 [-1.1, +0.5] |
| oracle | +7.1 [+2.7, +12.4] | -0.080 [-0.135, -0.036] | -0.6 [-1.2, +0.0] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +0.0 [+0.0, +0.0] | +0.000 [+0.000, +0.000] | +0.0 [+0.0, +0.0] |
| dynamic_perfect_perception | +1.8 [+0.0, +4.4] | -0.017 [-0.035, -0.003] | -0.4 [-0.7, -0.1] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.021 [0.008, 0.038]
