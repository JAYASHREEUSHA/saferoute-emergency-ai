# grid 6x10 | lambda=60 | perception=noisy (recall=0.9, fp=0.1, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.219 |
| static_risk | 90.5 [86.0, 94.5] | 0.188 [0.148, 0.236] | 23.0 / 44.5 | 11.6 | 0.7 | 0.04 | 1.409 |
| dynamic_risk | 92.0 [88.0, 95.5] | 0.179 [0.141, 0.225] | 23.5 / 44.7 | 11.1 | 0.6 | 0.05 | 2.090 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 1.967 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +3.0 [+0.0, +6.0] | -0.025 [-0.055, +0.005] | +0.4 [-0.1, +0.9] |
| dynamic_risk | +4.5 [+1.5, +7.5] | -0.034 [-0.062, -0.005] | +0.6 [+0.0, +1.2] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.009 [-0.022, -0.000] | +0.1 [-0.2, +0.3] |
| dynamic_perfect_perception | +3.5 [+1.0, +6.5] | -0.038 [-0.061, -0.020] | -0.7 [-1.1, -0.3] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.206 |
| static_risk | 79.0 [70.4, 87.7] | 0.394 [0.313, 0.478] | 29.3 / 46.3 | 25.6 | 1.3 | 0.11 | 1.317 |
| dynamic_risk | 81.5 [72.8, 90.1] | 0.385 [0.306, 0.468] | 30.4 / 58.4 | 25.0 | 1.3 | 0.06 | 2.233 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 2.072 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +9.9 [+3.7, +17.3] | -0.124 [-0.184, -0.069] | -0.6 [-1.6, +0.2] |
| dynamic_risk | +12.3 [+6.2, +19.8] | -0.133 [-0.195, -0.075] | -0.1 [-1.3, +1.2] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.5 [+0.0, +6.2] | -0.009 [-0.021, +0.002] | +0.3 [-0.3, +1.0] |
| dynamic_perfect_perception | +6.2 [+1.2, +12.3] | -0.039 [-0.071, -0.013] | -0.4 [-0.9, -0.0] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.046 [0.028, 0.069]
