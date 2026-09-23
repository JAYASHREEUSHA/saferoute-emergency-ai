# grid 6x10 | lambda=60 | perception=noisy (recall=0.7, fp=0.05, latency=4.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.205 |
| static_risk | 90.5 [86.0, 94.5] | 0.183 [0.142, 0.229] | 22.7 / 40.2 | 12.4 | 0.6 | 0.06 | 1.346 |
| dynamic_risk | 92.5 [88.5, 96.0] | 0.173 [0.133, 0.219] | 23.9 / 46.7 | 11.7 | 0.5 | 0.06 | 1.952 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 1.878 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +3.0 [+0.0, +6.0] | -0.031 [-0.057, -0.005] | +0.1 [-0.3, +0.4] |
| dynamic_risk | +5.0 [+2.0, +8.0] | -0.040 [-0.064, -0.018] | +0.9 [+0.1, +2.0] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.0 [+0.5, +4.0] | -0.009 [-0.024, +0.005] | +0.5 [-0.1, +1.4] |
| dynamic_perfect_perception | +3.5 [+1.0, +6.0] | -0.032 [-0.053, -0.013] | -0.4 [-0.7, -0.1] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.203 |
| static_risk | 77.8 [69.1, 86.4] | 0.411 [0.331, 0.496] | 29.5 / 50.8 | 29.1 | 1.3 | 0.11 | 1.275 |
| dynamic_risk | 81.5 [72.8, 90.1] | 0.403 [0.323, 0.489] | 31.5 / 60.6 | 27.8 | 1.3 | 0.09 | 2.062 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 1.989 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +8.6 [+2.5, +16.0] | -0.107 [-0.165, -0.052] | -0.4 [-1.4, +0.5] |
| dynamic_risk | +12.3 [+6.2, +19.8] | -0.115 [-0.170, -0.065] | +1.0 [-1.0, +3.8] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.008 [-0.036, +0.022] | +1.1 [-0.5, +3.4] |
| dynamic_perfect_perception | +7.4 [+2.5, +13.6] | -0.056 [-0.095, -0.024] | -0.6 [-1.3, -0.0] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.040 [0.023, 0.060]
