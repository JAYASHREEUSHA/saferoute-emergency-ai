# Difficulty sweep (60 scenarios per setting)

| difficulty | oracle success % | dynamic success % | dose vs shortest_path [95% CI] |
|---|---|---|---|
| easy (base) | 91.7 | 91.7 | -0.069 [-0.135, -0.012] |
| faster fire | 76.7 | 75.0 | -0.054 [-0.112, -0.001] |
| later warning | 51.7 | 51.7 | -0.116 [-0.181, -0.057] |
| faster+later warn | 23.3 | 20.0 | -0.017 [-0.059, +0.018] |

Oracle success % dropping toward 0 means most scenarios are unwinnable by ANY policy at that difficulty — a shrinking dose gap there reflects a harder benchmark, not a worse method. Read the dose gap alongside the oracle rate, not in isolation.
