# Lambda sweep (150 scenarios per value)

| lambda | dynamic success % | dynamic mean dose | dynamic mean time (s) | dose vs shortest_path [95% CI] |
|---|---|---|---|---|
| 0 | 89.3 | 0.202 | 22.7 | -0.036 [-0.070, -0.005] |
| 15 | 90.7 | 0.186 | 23.1 | -0.053 [-0.085, -0.023] |
| 30 | 91.3 | 0.179 | 23.2 | -0.060 [-0.092, -0.027] |
| 60 | 92.0 | 0.176 | 23.5 | -0.063 [-0.096, -0.030] |
| 120 | 92.0 | 0.177 | 23.6 | -0.062 [-0.095, -0.030] |
| 250 | 92.0 | 0.176 | 23.9 | -0.062 [-0.095, -0.030] |

lambda=0 reduces dynamic_risk to hazard-blind shortest-path routing (sanity check: its dose gap vs shortest_path should be ~0). Pick the smallest lambda where the dose gap's upper CI bound is clearly negative, then check mean time hasn't grown much.
