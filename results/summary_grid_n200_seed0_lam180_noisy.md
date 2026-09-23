# grid 6x10 | lambda=180 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.197 |
| static_risk | 92.0 [88.0, 95.5] | 0.168 [0.129, 0.214] | 22.7 / 41.1 | 11.1 | 0.5 | 0.07 | 1.301 |
| dynamic_risk | 94.0 [90.5, 97.0] | 0.153 [0.116, 0.196] | 23.3 / 44.8 | 10.3 | 0.5 | 0.04 | 1.925 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.147 [0.109, 0.190] | 24.3 / 46.8 | 9.4 | 0.5 | 0.04 | 1.808 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +4.5 [+1.0, +8.0] | -0.046 [-0.073, -0.016] | -0.2 [-0.5, +0.1] |
| dynamic_risk | +6.5 [+3.5, +10.0] | -0.060 [-0.086, -0.034] | +0.0 [-0.4, +0.5] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.067 [-0.093, -0.041] | +1.2 [+0.4, +2.1] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +2.0 [+0.5, +4.0] | -0.014 [-0.028, -0.004] | -0.0 [-0.2, +0.2] |
| dynamic_perfect_perception | +2.0 [+0.5, +4.0] | -0.021 [-0.037, -0.008] | +1.2 [+0.5, +2.1] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.196 |
| static_risk | 81.5 [72.8, 88.9] | 0.378 [0.301, 0.456] | 29.3 / 49.5 | 26.4 | 1.1 | 0.10 | 1.193 |
| dynamic_risk | 85.2 [77.8, 92.6] | 0.359 [0.283, 0.437] | 30.4 / 57.8 | 24.9 | 1.1 | 0.06 | 2.003 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.346 [0.270, 0.429] | 33.7 / 58.4 | 22.9 | 1.1 | 0.09 | 1.921 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +12.3 [+4.9, +21.0] | -0.139 [-0.203, -0.078] | -1.0 [-1.8, -0.2] |
| dynamic_risk | +16.0 [+8.6, +24.7] | -0.159 [-0.223, -0.100] | -0.5 [-1.7, +0.6] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.172 [-0.233, -0.112] | +3.6 [+1.0, +6.4] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.019 [-0.039, -0.004] | +0.1 [-0.4, +0.6] |
| dynamic_perfect_perception | +3.7 [+0.0, +8.6] | -0.033 [-0.058, -0.009] | +3.7 [+1.8, +5.9] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.020 [0.011, 0.033]
