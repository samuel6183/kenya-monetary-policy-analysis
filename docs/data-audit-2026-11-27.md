# Audited dataset | 27 November 2026

**Canonical file:** `data/processed/kenya_monetary_policy_audited.csv`. This supersedes the preliminary manually assembled policy/inflation series for empirical analysis. It is a source-reconciled research release, not certification by CBK, KNBS or an independent auditor.

## Scope and validation

- Monthly national indicators, November 2016–September 2026 inclusive; 119 unique consecutive months, 14 numeric series, one CPI base field and date.
- Core CBR, lending, CPI and published annual inflation are complete. Eleven numeric series are complete. No fabricated observations, forward filling or interpolation.
- 39 CPI values are published on February 2009=100 (Nov 2016–Jan 2020); 80 on February 2019=100 (Feb 2020–Sep 2026). Do not calculate CPI-level growth across the rebasing boundary. The index is not spliced.
- For 95 months with an in-sample lag 12 months earlier on the same CPI base, the absolute difference between published inflation and CPI-derived year-on-year inflation was at most 0.01631 percentage points (rounded source values). Twelve initial months and twelve cross-base months cannot undergo that within-panel check. This is an internal consistency test, not an independent verification of every observation.
- 74 numeric cells remain missing: one 182-day bill (April 2017), 32 repo and 41 reverse repo. Blank means unavailable or not verified, not zero. Other series have no missing cells. Repo gaps may represent no transactions; no such assumption is made.
- File SHA-256: `444a98058e22f669b103385227511d0f149e39b9644f5b0f40df6fffbd2c714e`. Git blob: `007731a241049880c1834ce38b70f1f85f1c8`.

## Source provenance

Original Colab collection procedure restored through [workflow run 45919079979](https://github.com/samuel6183/kenya-monetary-policy-analysis/actions/runs/45919079979). [Artifact 15163696971](https://github.com/samuel6183/kenya-monetary-policy-analysis/actions/runs/45919079979/artifacts/15163696971) contains raw source snapshots, PDF reports, catalogue, extracted candidates and CBK panel. Archive SHA-256: `963da2ec1aa3f49a813950506006da6a3fd322b3f4f4bd7b1ca536ba89ded7a3`. Artifacts are time-limited, so preserve locally if needed.

- CBK central bank rates: [original CSV](https://www.centralbank.go.ke/uploads/interest_rates/648402325_Central%20Bank%20Rates_with%20Heads.csv), SHA-256 `1ddfc361bf28defd4eea7e98c8e2885dffd6d028003e259500391e1012b8bef6`. Rates as published; not redefined as monthly averages where the original table does not specify.
- [CBK commercial banks weighted average rates](https://www.centralbank.go.ke/commercial-banks-weighted-average-rates/), table 17 AJAX pagination: 425 raw rows. September 2023 values (deposit 8.64, savings 4.00, lending 13.98, overdraft 13.62) independently checked against downloaded [CBK September 2023 Monthly Economic Indicators](https://www.centralbank.go.ke/uploads/monthly_economic_indicators/476370057_Monthly%20Economic%20Indicators%20September%202023.pdf), PDF page 12, Table 2.3, SHA-256 `86f50ebe753a939a0c97f634da1b4ddf281d7f235952d92582dd90a32356f805`.
- CPI from archived KNBS LEI tables; see `data/processed/cpi_source_manifest.csv` for month ranges, report UUID, physical PDF page and source-file hash. Candidate parsing used explicit table headings, annual headings and national CPI column. Only known-base observations were accepted; disagreements were inspected. Independent human cell-by-cell audit has not been performed.
- Annual inflation: [CBK 12-month inflation table](https://www.centralbank.go.ke/inflation-rates/) (KNBS origin) through July 2026, with corrections below; Aug and Sep 2026 from KNBS September 2026 LEI Table 1(b). The recovered archive included an earlier transcribed series; corrected values were compared against the published table and extracted KNBS candidates. Same-base CPI consistency additionally checked for 95 months.
- [KNBS September 2026 LEI](https://www.knbs.or.ke/wp-content/uploads/2026/11/Kenya-Leading-Economic-Indicators-September-2026.pdf), tables 1(a), 1(b), 3. 2026 values marked provisional in Table 3.

## Reconciliation log

| Month | Variable | Earlier value(s) | Adopted | Reason |
|---|---|---|---|---|
| May 2019 | INFLATION_YOY | 4.49 | 5.49 | [Original KNBS release](https://www.knbs.or.ke/consumer-price-indices-and-inflation-rates-for-may-2019/) and CPI consistency |
| May 2022 | KENYA_CPI | 123.12 / 133.01 | 123.12 | [KNBS May 2022 LEI](https://www.knbs.or.ke/wp-content/uploads/2023/07/Kenya-Leading-Economic-Indicators-May-2022.pdf); 133.01 is May 2023 in extracted evidence |
| May 2024 | INFLATION_YOY | 5.10 | 4.98 | [KNBS May 2024 LEI Table 1(b)](https://www.knbs.or.ke/wp-content/uploads/2024/07/Leading-Economic-Indicators-May-2024.pdf); later [December 2024 CPI report](https://www.knbs.or.ke/wp-content/uploads/2024/12/Kenya-Consumer-Price-Indices-and-Inflation-Rates-December-2024.pdf) confirms 5.0 rounded and CPI 139.64; initial release reported CPI 139.85 |
| June 2024 | INFLATION_YOY | 6.22 | 4.64 | Archived KNBS LEI table; [KNBS June 2024 release](https://www.knbs.or.ke/reports/consumer-price-indices-and-inflation-rates-june-2024/) confirms 4.6 rounded |
| February 2026 | DEPOSIT | 6.82 / 6.92 | 6.92 | KNBS Sep 2026 LEI Table 3 (CBK source) |
| February 2026 | SAVINGS | 2.41 / 3.17 | 3.17 | KNBS Sep 2026 LEI Table 3 (CBK source) |
| August 2026 | INFLATION_YOY | not in older CBK page | 6.59 | KNBS Sep 2026 LEI Table 1(b) |
| September 2026 | INFLATION_YOY / CPI | not in older CBK page | 6.76 / 156.47 | KNBS Sep 2026 LEI Tables 1(a,b) |

For non-conflicting native CBK rows, retain CBK as primary source. Differences identified versus KNBS Sep 2026 Table 3 (May 2026 deposit CBK 6.80 vs KNBS 6.86; June 2026 lending 14.38 vs 14.37; July 2026 91-day 8.80 vs 8.81; September 2026 364-day 9.06 vs 9.07) remain disclosed, not silently averaged. The CBK September 2023 bulletin corroborates the commercial row, not necessarily all central bank values; releases can differ in vintage and revisions. This is a retrospective research snapshot, not real-time vintage data. Three decimal places in the CSV are formatting, not additional measured precision.

## Use and limitations

All rate columns are percent; CPI is an index with the indicated base. Month is YYYY-MM. Commercial rates are weighted average rates. Treasury bill series distinguish tenors. No sector-specific livestock variables are included, so this dataset cannot alone identify agricultural or household-level effects. Check institutional reuse terms before redistributing raw publications. The previous forecast outputs were based on preliminary data and must be regenerated from the canonical file.

Run `python -m src.audit_dataset` to recheck coverage, consistency and exact snapshot hash. Run `python -m src.analysis --input data/processed/kenya_monetary_policy_audited.csv` to generate updated core models. The audit does not resolve endogeneity or replace econometric diagnostic testing.
