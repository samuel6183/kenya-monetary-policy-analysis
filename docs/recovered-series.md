# Recovered monthly policy and inflation series

Retrieved 27 November 2026 from CBK:
- https://www.centralbank.go.ke/rates/central-bank-rate/
- https://www.centralbank.go.ke/inflation-rates/ (original source KNBS; use 12-month inflation, not annual average).

Manually transcribed published numerical values for Nov 2016–Sep 2026. April 2019 identical duplicate removed. Month-end CBR is the last effective policy rate carried forward from dated decisions; it is not a monthly average. The event CSV contains rate changes and the initial pre-window decision. The recovered two-variable dataset has 119 unique months and no missing values. Independent comparison against full KNBS archive remains outstanding. Historical inflation values use the currently published vintage.

The 12-month expanding one-step holdout runs Oct 2025–Sep 2026, with the initial 107 months used for training. AR(1) and persistence were evaluated numerically using the recovered observations. The metrics CSV records actual calculations. Python reproduction: python -m src.policy_forecast. This is a preliminary retrospective evaluation, not a real-time forecast or a causal model.

Commercial bank lending remains available only for Jan–Sep 2026 in the collected artifact. Full multivariate analysis is blocked by this gap. The CPI level and other interest rate series are not recovered by this release.
