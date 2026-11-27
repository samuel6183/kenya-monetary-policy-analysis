# Empirical methodology and data provenance

Target period: November 2016 through September 2026 (119 monthly periods), aligned to the previously collected dataset. The earlier README mentioned October; that extra month is not silently included.

Official sources:
- CBK central bank rates: https://www.centralbank.go.ke/central-bank-rates/
- CBK commercial weighted average rates: https://www.centralbank.go.ke/commercial-banks-weighted-average-rates/
- KNBS CPI: https://www.knbs.or.ke/statistical-releases/
- June 2022 CPI release: https://www.knbs.or.ke/consumer-price-indices-and-inflation-rates-for-june-2022/

HTML collection is best effort; server-side pagination may hide records. Downloaded HTML and checksums preserve provenance. PDF text matches are candidate pages only. Enter verified CPI observations into the template with page, base and source. CPI levels across rebasing periods must not be joined without a documented linking procedure. Use published year-on-year inflation in the core model.

Conflicting values for a month/variable are withheld, not averaged. For example, the CBK commercial rates page has conflicting deposit and savings values for February 2026. Lending agrees in both rows; preserve the agreed value and flag the conflicts. Missing values remain missing. Do not model an irregularly spaced sequence by dropping interior months.

The core model uses monthly changes in CBR and lending rates and year-on-year inflation. Lagged associations are descriptive, not causal estimates: monetary policy responds to inflation and omitted shocks. ADF is a diagnostic with limited power. HAC standard errors account for some serial dependence, not endogeneity. Chronological one-step inflation forecasts use only earlier observations; compare AR(1) against persistence. No final empirical findings until the actual full panel has been validated.
