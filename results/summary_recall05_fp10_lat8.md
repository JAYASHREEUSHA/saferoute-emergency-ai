# grid 6x10 | lambda=60 | perception=noisy (recall=0.5, fp=0.1, latency=8.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.239 |
| static_risk | 88.0 [83.5, 92.5] | 0.224 [0.178, 0.273] | 22.9 / 44.0 | 14.3 | 0.8 | 0.04 | 1.577 |
| dynamic_risk | 91.0 [87.0, 94.5] | 0.204 [0.162, 0.252] | 23.9 / 44.9 | 13.0 | 0.7 | 0.07 | 2.167 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 2.132 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +0.5 [-2.5, +3.5] | +0.010 [-0.016, +0.040] | +0.5 [+0.1, +1.1] |
| dynamic_risk | +3.5 [+1.0, +6.0] | -0.009 [-0.031, +0.014] | +1.0 [+0.4, +1.7] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.0 [+1.0, +5.5] | -0.020 [-0.042, -0.000] | +0.3 [-0.1, +0.7] |
| dynamic_perfect_perception | +6.0 [+3.0, +9.5] | -0.074 [-0.104, -0.046] | -0.9 [-1.4, -0.4] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.231 |
| static_risk | 75.3 [65.4, 84.0] | 0.472 [0.387, 0.560] | 29.3 / 47.4 | 31.2 | 1.7 | 0.06 | 1.490 |
| dynamic_risk | 77.8 [67.9, 86.4] | 0.461 [0.376, 0.549] | 30.4 / 55.9 | 30.4 | 1.7 | 0.09 | 2.196 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 2.224 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +6.2 [+0.0, +12.3] | -0.046 [-0.097, +0.001] | -0.4 [-1.0, +0.2] |
| dynamic_risk | +8.6 [+3.7, +14.8] | -0.057 [-0.107, -0.013] | -0.3 [-1.3, +0.6] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.5 [+0.0, +6.2] | -0.011 [-0.036, +0.010] | +0.3 [-0.6, +1.0] |
| dynamic_perfect_perception | +9.9 [+3.7, +17.3] | -0.117 [-0.174, -0.067] | -0.6 [-1.5, +0.1] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.071 [0.047, 0.099]
