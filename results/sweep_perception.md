# Detector-noise sweep (150 scenarios per setting)

| detector | recall | fp rate | latency (s) | dynamic success % | dose vs shortest_path [95% CI] |
|---|---|---|---|---|---|
| perfect | n/a | n/a | n/a | 92.0 | -0.063 [-0.096, -0.031] |
| good (default) | 0.90 | 0.010 | 2.0 | 92.0 | -0.063 [-0.096, -0.030] |
| moderate | 0.75 | 0.030 | 4.0 | 92.0 | -0.050 [-0.085, -0.015] |
| poor | 0.55 | 0.080 | 6.0 | 89.3 | -0.037 [-0.065, -0.012] |
| very poor | 0.35 | 0.150 | 8.0 | 87.3 | -0.007 [-0.043, +0.030] |

'good (default)' matches the noise levels assumed in Step 2's headline results. 'perfect' is the ceiling (routing logic alone, no perception error). Replace 'good (default)' with numbers from scripts/calibrate_perception.py once the fire/smoke model is trained.
