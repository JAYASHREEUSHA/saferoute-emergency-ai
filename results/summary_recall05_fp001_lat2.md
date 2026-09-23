# grid 6x10 | lambda=60 | perception=noisy (recall=0.5, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.265 |
| static_risk | 91.0 [87.0, 95.0] | 0.187 [0.144, 0.236] | 22.6 / 42.2 | 12.9 | 0.6 | 0.04 | 1.697 |
| dynamic_risk | 92.5 [88.5, 96.0] | 0.172 [0.130, 0.217] | 22.9 / 44.3 | 11.6 | 0.6 | 0.03 | 2.374 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 2.363 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +3.5 [+0.0, +7.0] | -0.026 [-0.054, +0.002] | -0.2 [-0.5, +0.1] |
| dynamic_risk | +5.0 [+2.0, +8.5] | -0.042 [-0.068, -0.017] | -0.1 [-0.4, +0.3] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.015 [-0.030, -0.003] | -0.1 [-0.2, +0.0] |
| dynamic_perfect_perception | +3.0 [+1.0, +5.5] | -0.037 [-0.061, -0.016] | -0.2 [-0.4, +0.1] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.267 |
| static_risk | 80.2 [71.6, 88.9] | 0.418 [0.338, 0.502] | 29.4 / 55.6 | 29.2 | 1.4 | 0.09 | 1.619 |
| dynamic_risk | 82.7 [74.1, 90.1] | 0.400 [0.323, 0.483] | 29.9 / 53.7 | 27.9 | 1.3 | 0.05 | 2.436 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 2.490 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +11.1 [+3.7, +18.5] | -0.100 [-0.159, -0.045] | -0.9 [-1.8, -0.1] |
| dynamic_risk | +13.6 [+7.4, +22.2] | -0.118 [-0.178, -0.063] | -0.9 [-1.8, -0.2] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.5 [+0.0, +6.2] | -0.018 [-0.040, -0.001] | -0.1 [-0.3, +0.1] |
| dynamic_perfect_perception | +4.9 [+1.2, +9.9] | -0.063 [-0.104, -0.027] | -0.2 [-0.9, +0.4] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.039 [0.022, 0.060]
