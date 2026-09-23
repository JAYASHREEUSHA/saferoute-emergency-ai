# grid 6x10 | lambda=60 | perception=noisy (recall=0.9, fp=0.01, latency=8.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.206 |
| static_risk | 91.0 [86.5, 95.0] | 0.179 [0.139, 0.226] | 22.5 / 39.5 | 12.3 | 0.5 | 0.04 | 1.364 |
| dynamic_risk | 93.0 [89.0, 96.0] | 0.166 [0.129, 0.211] | 23.1 / 43.3 | 10.9 | 0.5 | 0.03 | 1.965 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 1.888 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +3.5 [+0.5, +6.5] | -0.034 [-0.059, -0.011] | -0.1 [-0.4, +0.2] |
| dynamic_risk | +5.5 [+2.5, +8.5] | -0.047 [-0.073, -0.023] | -0.1 [-0.4, +0.2] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.0 [+0.5, +4.0] | -0.013 [-0.027, -0.001] | +0.0 [-0.1, +0.1] |
| dynamic_perfect_perception | +3.0 [+1.0, +5.5] | -0.029 [-0.049, -0.012] | -0.2 [-0.4, +0.0] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.206 |
| static_risk | 77.8 [69.1, 86.4] | 0.413 [0.330, 0.498] | 29.0 / 46.2 | 29.5 | 1.3 | 0.10 | 1.296 |
| dynamic_risk | 82.7 [74.1, 90.1] | 0.385 [0.307, 0.466] | 30.2 / 53.5 | 25.9 | 1.2 | 0.05 | 2.052 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 2.007 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +8.6 [+2.5, +16.0] | -0.105 [-0.165, -0.050] | -1.0 [-1.8, -0.3] |
| dynamic_risk | +13.6 [+6.2, +21.0] | -0.133 [-0.193, -0.077] | -1.0 [-1.9, -0.3] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +4.9 [+1.2, +9.9] | -0.028 [-0.058, -0.006] | -0.0 [-0.2, +0.2] |
| dynamic_perfect_perception | +7.4 [+2.5, +13.6] | -0.058 [-0.095, -0.025] | -0.1 [-0.6, +0.5] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.033 [0.019, 0.050]
