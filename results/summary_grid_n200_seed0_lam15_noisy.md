# grid 6x10 | lambda=15 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.203 |
| static_risk | 91.0 [86.5, 95.0] | 0.176 [0.135, 0.223] | 22.1 / 39.2 | 11.8 | 0.6 | 0.04 | 1.344 |
| dynamic_risk | 92.5 [88.5, 96.0] | 0.167 [0.127, 0.212] | 22.5 / 39.5 | 11.1 | 0.6 | 0.01 | 1.880 |
| dynamic_perfect_perception | 92.5 [88.5, 96.0] | 0.165 [0.125, 0.211] | 22.4 / 39.4 | 10.9 | 0.6 | 0.01 | 1.858 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +3.5 [+1.0, +6.5] | -0.037 [-0.062, -0.013] | -0.3 [-0.6, -0.1] |
| dynamic_risk | +5.0 [+2.5, +8.0] | -0.047 [-0.072, -0.023] | -0.3 [-0.6, -0.1] |
| dynamic_perfect_perception | +5.0 [+2.5, +8.0] | -0.048 [-0.073, -0.025] | -0.4 [-0.7, -0.2] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.009 [-0.019, -0.002] | -0.1 [-0.2, -0.0] |
| dynamic_perfect_perception | +1.5 [+0.0, +3.5] | -0.011 [-0.021, -0.002] | -0.1 [-0.3, -0.0] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.201 |
| static_risk | 77.8 [67.9, 86.4] | 0.411 [0.327, 0.498] | 28.1 / 44.8 | 28.5 | 1.4 | 0.11 | 1.299 |
| dynamic_risk | 81.5 [72.8, 90.1] | 0.392 [0.312, 0.476] | 29.0 / 46.7 | 26.8 | 1.4 | 0.04 | 1.966 |
| dynamic_perfect_perception | 81.5 [72.8, 90.1] | 0.392 [0.313, 0.478] | 29.0 / 46.7 | 26.6 | 1.4 | 0.04 | 1.946 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +8.6 [+2.5, +16.0] | -0.107 [-0.166, -0.053] | -1.3 [-2.1, -0.6] |
| dynamic_risk | +12.3 [+6.2, +19.8] | -0.126 [-0.185, -0.073] | -1.3 [-2.1, -0.6] |
| dynamic_perfect_perception | +12.3 [+6.2, +19.8] | -0.126 [-0.183, -0.072] | -1.3 [-2.1, -0.6] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.019 [-0.040, -0.004] | -0.2 [-0.5, -0.0] |
| dynamic_perfect_perception | +3.7 [+0.0, +8.6] | -0.019 [-0.042, +0.003] | -0.2 [-0.5, +0.1] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.034 [0.019, 0.052]
