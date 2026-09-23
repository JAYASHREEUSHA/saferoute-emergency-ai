# grid 6x10 | lambda=60 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.218 |
| static_risk | 92.5 [88.5, 96.0] | 0.163 [0.124, 0.207] | 22.5 / 41.0 | 11.1 | 0.5 | 0.04 | 1.402 |
| dynamic_risk | 94.0 [90.5, 97.0] | 0.153 [0.117, 0.196] | 23.0 / 44.2 | 10.2 | 0.5 | 0.01 | 2.086 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.150 [0.113, 0.193] | 23.0 / 44.2 | 9.8 | 0.5 | 0.02 | 1.953 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +5.0 [+2.0, +8.5] | -0.050 [-0.076, -0.023] | -0.3 [-0.6, -0.0] |
| dynamic_risk | +6.5 [+3.5, +10.0] | -0.060 [-0.086, -0.034] | -0.3 [-0.6, +0.0] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.063 [-0.090, -0.037] | -0.3 [-0.6, -0.0] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.010 [-0.019, -0.002] | -0.0 [-0.2, +0.1] |
| dynamic_perfect_perception | +1.5 [+0.0, +3.5] | -0.013 [-0.024, -0.003] | -0.0 [-0.2, +0.1] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.219 |
| static_risk | 81.5 [72.8, 88.9] | 0.379 [0.301, 0.457] | 29.1 / 45.3 | 26.6 | 1.1 | 0.10 | 1.323 |
| dynamic_risk | 85.2 [77.8, 92.6] | 0.359 [0.283, 0.437] | 30.1 / 54.2 | 24.7 | 1.1 | 0.04 | 2.287 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.355 [0.278, 0.435] | 30.2 / 54.2 | 23.9 | 1.1 | 0.05 | 2.110 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +12.3 [+4.9, +21.0] | -0.139 [-0.203, -0.077] | -1.1 [-2.0, -0.4] |
| dynamic_risk | +16.0 [+8.6, +24.7] | -0.159 [-0.223, -0.101] | -1.0 [-1.9, -0.2] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.163 [-0.228, -0.103] | -0.9 [-1.8, -0.1] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.019 [-0.040, -0.004] | -0.0 [-0.4, +0.4] |
| dynamic_perfect_perception | +3.7 [+0.0, +8.6] | -0.024 [-0.049, -0.001] | +0.1 [-0.4, +0.5] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.021 [0.011, 0.033]
