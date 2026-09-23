# grid 6x10 | lambda=30 | perception=noisy (recall=0.9, fp=0.01, latency=2.0s)

Scenarios: 200 (paired: every policy sees the same scenario and detector noise)

## All scenarios

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 87.5 [82.5, 92.0] | 0.213 [0.166, 0.265] | 22.0 / 40.8 | 13.1 | 0.8 | 0.06 | 0.209 |
| static_risk | 91.5 [87.5, 95.0] | 0.171 [0.130, 0.217] | 22.2 / 39.3 | 10.9 | 0.6 | 0.04 | 1.309 |
| dynamic_risk | 93.0 [89.0, 96.0] | 0.161 [0.122, 0.205] | 22.6 / 40.9 | 10.2 | 0.6 | 0.01 | 1.931 |
| dynamic_perfect_perception | 93.5 [90.0, 96.5] | 0.157 [0.118, 0.201] | 22.8 / 42.0 | 9.9 | 0.6 | 0.02 | 1.846 |
| oracle | 94.0 [90.5, 97.0] | 0.133 [0.096, 0.174] | 26.8 / 53.4 | 4.6 | 0.2 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +4.0 [+1.0, +7.0] | -0.043 [-0.068, -0.017] | -0.3 [-0.6, -0.1] |
| dynamic_risk | +5.5 [+2.5, +8.5] | -0.052 [-0.079, -0.026] | -0.3 [-0.6, -0.1] |
| dynamic_perfect_perception | +6.0 [+3.0, +9.0] | -0.057 [-0.082, -0.031] | -0.4 [-0.6, -0.1] |
| oracle | +6.5 [+3.5, +10.0] | -0.081 [-0.109, -0.054] | +3.4 [+2.0, +4.8] |

Is live re-planning better than planning once?

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +1.5 [+0.0, +3.5] | -0.009 [-0.019, -0.002] | -0.1 [-0.2, -0.0] |
| dynamic_perfect_perception | +2.0 [+0.5, +4.0] | -0.014 [-0.025, -0.004] | -0.1 [-0.3, +0.1] |

## Hazard-relevant scenarios (81 of 200: the shortest route gets dose >= 0.05 or fails)

| Policy | Success % [95% CI] | Mean dose [95% CI] | Time s (succ.) mean / p95 | Smoke s | Fire s | Reroutes | Plan ms |
|---|---|---|---|---|---|---|---|
| shortest_path | 69.1 [58.0, 79.0] | 0.518 [0.433, 0.607] | 28.7 / 49.9 | 32.1 | 2.1 | 0.15 | 0.204 |
| static_risk | 79.0 [69.1, 87.7] | 0.397 [0.316, 0.484] | 28.3 / 44.8 | 26.3 | 1.4 | 0.11 | 1.215 |
| dynamic_risk | 82.7 [74.1, 90.1] | 0.378 [0.300, 0.465] | 29.2 / 46.7 | 24.7 | 1.4 | 0.04 | 2.049 |
| dynamic_perfect_perception | 84.0 [75.3, 91.4] | 0.371 [0.293, 0.459] | 29.7 / 53.0 | 24.3 | 1.3 | 0.05 | 1.969 |
| oracle | 85.2 [77.8, 92.6] | 0.322 [0.244, 0.406] | 36.5 / 62.8 | 11.2 | 0.5 | 0.00 | 0.000 |

Paired differences vs `shortest_path` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| static_risk | +9.9 [+3.7, +17.3] | -0.121 [-0.183, -0.061] | -1.2 [-2.1, -0.6] |
| dynamic_risk | +13.6 [+7.4, +22.2] | -0.140 [-0.200, -0.083] | -1.3 [-2.1, -0.6] |
| dynamic_perfect_perception | +14.8 [+7.4, +23.5] | -0.147 [-0.208, -0.090] | -1.2 [-2.0, -0.5] |
| oracle | +16.0 [+8.6, +24.7] | -0.196 [-0.260, -0.134] | +5.6 [+2.3, +9.6] |

Live re-planning vs planning once (hazard-relevant scenarios):

Paired differences vs `static_risk` (negative dose / positive success = better):

| Policy | d Success (pp) [95% CI] | d Dose [95% CI] | d Time s, both succeed [95% CI] |
|---|---|---|---|
| dynamic_risk | +3.7 [+0.0, +8.6] | -0.019 [-0.040, -0.004] | -0.2 [-0.5, -0.0] |
| dynamic_perfect_perception | +4.9 [+1.2, +9.9] | -0.027 [-0.053, -0.003] | -0.1 [-0.5, +0.3] |

Regret of `dynamic_risk` vs hindsight oracle (mean dose, all scenarios): 0.028 [0.015, 0.045]
