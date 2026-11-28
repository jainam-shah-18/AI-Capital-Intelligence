# Data Dictionary

## 1. Source

The project extracts company-wide financial observations from the SEC EDGAR Company Facts API for:

- Amazon (AMZN)
- Microsoft (MSFT)
- Alphabet (GOOGL)
- Meta Platforms (META)

The source contains reported company financial facts. It does not identify spending or returns attributable exclusively to AI.

## 2. Core financial metrics

| Metric | Business meaning | Typical interpretation |
|---|---|---|
| REVENUE | Reported company revenue | Scale of business activity |
| OPERATING_INCOME | Income from operating activities | Operating profitability |
| NET_INCOME | Profit after expenses and applicable taxes | Overall reported profitability |
| CAPITAL_EXPENDITURE | Reported capital investment / expenditure | Investment in long-lived assets |
| OPERATING_CASH_FLOW | Cash generated from operating activities | Cash-generation capacity |

Exact source tags, units, period alignment, and calculation rules must be checked in the corresponding dbt models before interpreting individual values.

## 3. Important derived concepts

| Concept | Meaning | Caution |
|---|---|---|
| Company comparison | Compares reported metrics across companies and periods | Company fiscal periods may differ |
| Revenue forecast | Model-generated revenue estimates | Forecasts are not reported actuals |
| Financial anomaly | Potential unusual observation | A flag is not proof of misconduct or error |
| Risk indicator | Rule/model-based review signal | Requires human investigation |
| Pipeline monitoring | Execution and data-load observability | Operational health does not prove financial accuracy |

## 4. Data layers

| Layer | Purpose |
|---|---|
| Raw | Ingested source data |
| Staging | Source cleanup and standardization |
| Intermediate | Canonical metrics, classifications and period alignment |
| Marts | Analytics-ready business datasets |

## 5. Data quality

The latest verified dbt build completed with:

- 94 successful build steps
- 72 data tests
- 0 warnings
- 0 errors
- 0 skipped steps

This is a build summary, not 94 data tests.

## 6. Interpretation and governance

- Preserve the original reporting period and unit when comparing observations.
- Do not treat missing values as zero.
- Do not present forecast values as actual financial results.
- Do not describe company-wide financial metrics as AI-specific ROI.
- `FREE_CASH_FLOW` remains NULL where the calculation basis is not approved.
- `FREE_CASH_FLOW_CANDIDATE` is not an approved free-cash-flow measure.
- Investigate anomaly and risk flags before making business decisions.

## 7. Authoritative implementation references

For exact source tags and transformation logic, inspect:

- `src/aci/` — ingestion and transformation code
- `dbt/models/staging/` — staging models
- `dbt/models/intermediate/` — intermediate models
- `dbt/models/marts/` — analytical marts
- `dbt/seeds/` — reference mappings
- `dbt/tests/` — data quality tests
