# grid 6x10 | lambda=120 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.225 |
| static_risk | 92.5 [88.5, 96.0] | 0.163 [0.124, 0.207] | 22.6 / 41.0 | 10.9 | 0.5 | 0.04 | 1.439 |
| dynamic_risk | 94.0 [90.5, 97.0] | 0.154 [0.117, 0.197] | 23.1 / 44.2 | 10.3 | 0.5 | 0.02 | 2.147 |
| dynamic_perfect_perception | 94.0 [90.5, 97.0] | 0.148 [0.110, 0.191] | 24.0 / 46.8 | 9.5 | 0.5 | 0.04 | 2.039 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +5.0 [+2.0, +8.5] | -0.051 [-0.076, -0.023] | -0.2 [-0.5, +0.1] |
| dynamic_risk | +6.5 [+3.5, +10.0] | -0.059 [-0.086, -0.033] | -0.1 [-0.5, +0.2] |
| dynamic_perfect_perception | +6.5 [+3.5, +10.0] | -0.065 [-0.092, -0.039] | +0.9 [+0.2, +1.7] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.009 [-0.017, -0.002] | -0.1 [-0.2, -0.0] |
| dynamic_perfect_perception | +1.5 [+0.0, +3.5] | -0.015 [-0.026, -0.005] | +0.9 [+0.3, +1.7] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.222 |
| static_risk | 81.5 [72.8, 88.9] | 0.378 [0.301, 0.456] | 29.3 / 49.5 | 26.4 | 1.1 | 0.10 | 1.341 |
| dynamic_risk | 85.2 [77.8, 92.6] | 0.361 [0.284, 0.439] | 30.3 / 57.8 | 25.0 | 1.1 | 0.05 | 2.302 |
| dynamic_perfect_perception | 85.2 [77.8, 92.6] | 0.349 [0.271, 0.430] | 32.9 / 60.2 | 23.2 | 1.1 | 0.10 | 2.241 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +12.3 [+4.9, +21.0] | -0.139 [-0.203, -0.078] | -1.0 [-1.8, -0.2] |
| dynamic_risk | +16.0 [+8.6, +24.7] | -0.157 [-0.222, -0.098] | -0.8 [-1.9, +0.2] |
| dynamic_perfect_perception | +16.0 [+8.6, +24.7] | -0.169 [-0.232, -0.108] | +2.7 [+0.4, +5.2] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.018 [-0.037, -0.004] | -0.2 [-0.5, +0.0] |
| dynamic_perfect_perception | +3.7 [+0.0, +8.6] | -0.029 [-0.055, -0.007] | +2.9 [+1.2, +5.0] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.021 [0.011, 0.034]
