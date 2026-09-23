# Ablations (150 scenarios, all vs shortest_path baseline)

| variant | success % | mean dose | dose vs shortest_path [95% CI] | mean reroutes |
|---|---|---|---|---|
| dynamic_risk (full) | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.02 |
| no_hysteresis | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.04 |
| no_crowd_term | 92.0 | 0.176 | -0.063 [-0.096, -0.030] | 0.02 |
| perfect_perception | 92.0 | 0.175 | -0.063 [-0.096, -0.031] | 0.02 |

no_hysteresis reroutes the instant a cheaper option appears (no switch margin) — compare its mean reroutes to the full method's. no_crowd_term disables crowd-based slowdown/cost. perfect_perception uses ground-truth hazards with no latency (upper bound on this policy).
