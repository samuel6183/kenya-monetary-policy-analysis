# Empirical research results — canonical dataset

Executed 27 November 2026 using the audited 119-month snapshot (SHA-256 444a98058e22f669b103385227511d0f149e39b9644f5b0f40df6fffbd2c714e). Local execution used pandas 2.2.3 and statsmodels 0.14.6. Reproduce with python -m src.research; the audited-research workflow also produces the full artifact.

## Findings
- Lagged monthly change in CBR is positively associated with change in lending: coefficient 0.177779, HAC 95% CI [0.112002, 0.243557], p=1.18e-7, n=117, R²=0.488522. Not a causal estimate.
- Inflation-change regression R²=0.071762, lagged CBR p=0.9635. The lending regression rejects residual independence (Ljung–Box p=.004127 at lag 6 and .003411 at lag 12). The inflation regression does not reject at 5% (p=.150969 at lag 6 and .056644 at lag 12), though it has low fit. This corrects the earlier diagnostic interpretation.
- ADF and KPSS evidence is mixed for differenced CBR and lending. VAR uses first differences as an exploratory specification. BIC selects lag 1, AIC lag 2. VAR(1) is stable, but residual whiteness p=0.000531 and normality rejected. Non-orthogonal impulse responses are descriptive, not identified structural shocks; conventional uncertainty bands are not reliable under failed assumptions.
- Expanding-window one-step inflation evaluation Oct 2024–Sep 2026, 24 months. VAR(2) RMSE 0.394003, ARIMA(1,1,0) 0.394461, AR(1) 0.419903, persistence 0.425451, seasonal naive 2.232500. AR(1) MAE 0.269199 narrowly beats VAR(2) 0.270426. VAR(2) forecast is a separate fixed specification, not the BIC-selected diagnostic VAR. No statistically established superiority; retrospective revised data, not vintage-aware real-time forecasts.
- Missing secondary rates are left blank; CPI base periods remain separate. National financial indicators do not identify sector-specific impacts on livestock producers or household welfare.

## Outputs
See outputs/audited/tables and outputs/audited/figures. All ten SVGs and full generated analytical tables are permanently committed. See the [working paper](../RESEARCH_PAPER.md), [PDF](../RESEARCH_PAPER.pdf) and [executed notebook](../notebooks/Research_Analysis.ipynb). Earlier two-series results are superseded.

## Further work
Test structural breaks, longer lags and robust specifications; consider integration and cointegration before claiming long-run effects. Independent source audit remains desirable. This research is not an ILRI study or endorsement.
