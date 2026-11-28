# AI Capital Intelligence — Technical Documentation

**Project:** AI Capital Intelligence (ACI)
**Documentation date:** 27 November 2026
**Status:** Local integrated pipeline validated; public application and dashboard deployment remain outstanding.

---

## 1. Purpose

This document describes the technical architecture, data engineering workflow, analytical transformations, orchestration, quality controls, and AI integration implemented in AI Capital Intelligence.

The system processes publicly available SEC financial information for Amazon, Microsoft, Alphabet, and Meta. It produces governed analytical datasets for financial performance analysis, comparison, cash-flow analysis, forecasting, anomaly detection, and risk monitoring.

The project is a portfolio implementation and is not represented as a fully deployed enterprise production service.

## 2. System Architecture

The principal data flow is:

1. Retrieve company financial facts from SEC EDGAR Company Facts.
2. Extract and normalize observations with Python.
3. Write processed CSV and Parquet datasets.
4. Store and load data through the configured AWS S3 and Snowflake integrations.
5. Transform and test warehouse data using dbt.
6. Orchestrate extraction, output validation, and dbt build using Airflow.
7. Expose analytical models to Power BI and the AI application.

### Logical architecture

```text
SEC EDGAR Company Facts API
            |
            v
    Python Ingestion Layer
    Extraction / Normalization
            |
            v
       CSV + Parquet
            |
       +----+----+
       |         |
       v         v
     AWS S3   Snowflake RAW
                 |
                 v
             STAGING
                 |
                 v
              dbt
                 |
       +---------+----------+
       |                    |
       v                    v
  INTERMEDIATE             MARTS
                            |
                  +---------+---------+
                  |         |         |
                  v         v         v
                Power BI   AI/RAG  Monitoring

       Apache Airflow coordinates execution
```

This is a logical view. It does not imply that every component is publicly hosted or continuously available.

## 3. Data Source and Scope

### SEC EDGAR Company Facts

The project uses the SEC Company Facts API to retrieve reported company financial facts.

Covered companies:

| Company | Ticker |
|---|---|
| Amazon | AMZN |
| Microsoft | MSFT |
| Alphabet | GOOGL |
| Meta Platforms | META |

Principal metrics:

- Revenue
- Operating income
- Net income
- Capital expenditure
- Operating cash flow

The SEC source provides company-level reported financial information. It does not provide a direct measure of AI-specific return on investment.

### Data interpretation

Financial facts may differ by company in:

- XBRL concept selection.
- Reporting duration.
- Fiscal-year calendar.
- Filing amendments.
- Units and dimensional context.
- Availability of quarterly versus year-to-date observations.

Consequently, normalization and eligibility rules are important before comparing observations.

## 4. Python Ingestion Layer

The Python pipeline is invoked from the repository root:

```bash
python -m src.aci.pipeline
```

Its responsibilities include:

- Extracting SEC financial observations.
- Normalizing records into a consistent schema.
- Processing the supported companies and metrics.
- Producing CSV and Parquet outputs.
- Supporting configured S3 and Snowflake integration.
- Recording execution information used by downstream monitoring.

Principal processed outputs:

```text
data/processed/financial_metrics.csv
data/processed/financial_metrics.parquet
```

A previously recorded successful extraction contained 4,529 observations across the four companies.

The actual row count can vary with source updates, extraction windows, and data eligibility rules.

## 5. Snowflake Warehouse Design

The warehouse separates source data from progressively standardized and analytical data.

| Layer | Responsibility |
|---|---|
| RAW | Ingested financial observations |
| STAGING | Standardization and filtering |
| ANALYTICS | Analytical source views |
| DBT_DEV | dbt development models and marts |

Configured development environment:

- Database: `ACI_DB`
- Schema: `DBT_DEV`
- Warehouse: `COMPUTE_WH`

Snowflake credentials are supplied through local environment configuration and must never be committed to source control.

For production, the current development access should be replaced with purpose-specific least-privilege roles.

## 6. dbt Transformation Architecture

The dbt project is located in the `dbt/` directory.

Run commands from that directory:

```bash
dbt debug
dbt build
```

The project contains 20 SQL models organized into three layers.

### 6.1 Staging models

| Model | Responsibility |
|---|---|
| `stg_sec_financial_observations` | Standardizes SEC financial observations |
| `stg_pipeline_run_log` | Prepares pipeline execution records |

### 6.2 Intermediate models

| Model | Responsibility |
|---|---|
| `int_financial_metric_canonical` | Canonical metric selection |
| `int_financial_observations_canonical` | Canonical observation preparation |
| `int_financial_observations_classified` | Observation classification |
| `int_financial_performance_metrics` | Financial performance metric preparation |
| `int_financial_period_alignment` | Reporting-period alignment |
| `int_financial_period_calendar` | Period calendar support |
| `int_financial_quarterly_cashflow_derived` | Quarterly cash-flow derivation |
| `int_metric_mapping_validation` | Metric mapping validation |
| `int_quarterly_financial_observations` | Quarterly observation preparation |

### 6.3 Mart models

| Model | Analytical purpose |
|---|---|
| `mart_financial_metrics` | Financial metric dataset |
| `mart_financial_metrics_canonical` | Canonical financial metrics |
| `mart_company_performance` | Company financial performance |
| `mart_company_comparison` | Peer-company comparison |
| `mart_cash_flow_analysis` | Cash-flow analysis |
| `mart_revenue_forecast` | Revenue forecasting |
| `mart_financial_anomalies` | Unusual financial pattern indicators |
| `mart_financial_risk_indicators` | Financial risk indicators |
| `mart_pipeline_run_monitoring` | Pipeline execution monitoring |

The repository contains 20 SQL models in total: 2 staging, 9 intermediate, and 9 marts.

### 6.4 Cash-flow derivation

Cumulative cash-flow observations must be converted carefully into discrete quarterly values.

The implemented derivation rules support:

- Q2 = first-half cumulative amount minus Q1.
- Q3 = nine-month cumulative amount minus first-half cumulative amount.
- Q4 = annual cumulative amount minus nine-month cumulative amount.

Reported standalone quarterly observations take precedence when available.

**Important accounting control:** CAPEX reporting-basis approval remains unresolved. The approved `FREE_CASH_FLOW` field is deliberately NULL where the basis is not approved. `FREE_CASH_FLOW_CANDIDATE` is an arithmetic candidate, not approved official free cash flow.

## 7. dbt Data Quality

The project contains:

- 20 SQL models.
- 2 seeds.
- 2 sources.
- 72 data tests.

The tests cover data completeness, accepted values, and model-specific integrity rules.

### Verified integrated build

The Airflow execution on 27 November 2026 produced this dbt log summary:

```text
Finished running 2 seeds, 5 table models,
72 data tests, 15 view models
in 0 hours 7 minutes and 10.12 seconds.

Completed successfully

PASS=94 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=94
```

This is a successful build of 94 total dbt execution steps, including 72 data tests. It must not be described as 94 data tests.

## 8. Apache Airflow Orchestration

DAG identifier:

`aci_sec_financial_pipeline`

The DAG defines three dependent tasks.

### Task 1 — run_sec_pipeline

Executes the Python SEC ingestion pipeline inside the Airflow environment.

### Task 2 — validate_pipeline_outputs

Validates the processed CSV and Parquet outputs, including expected company and metric coverage.

### Task 3 — run_dbt_build

Runs the dbt build against the configured Snowflake development target. The task uses an isolated project copy and writes a dedicated log for the DAG run.

### Reliability configuration

The current DAG configuration includes:

- Maximum active DAG runs: 1.
- DAG-run timeout: 70 minutes.
- SEC task timeout: 30 minutes.
- Validation task timeout: 5 minutes.
- dbt task timeout: 30 minutes.
- Retry count: 2.
- Retry delay: 5 minutes.

### Verified execution on 27 November 2026

| Task | State |
|---|---|
| `run_sec_pipeline` | SUCCESS |
| `validate_pipeline_outputs` | SUCCESS |
| `run_dbt_build` | SUCCESS |

All three tasks succeeded in the same manual DAG run.

The dbt log recorded 94 successful steps with no warnings, errors, or skipped steps.

Airflow runs in Docker Compose for local development. Its successful local execution does not establish public cloud availability.

## 9. Power BI Semantic Model and Report

The repository includes a Power BI report and project source files.

The seven report pages cover:

1. Financial Performance
2. Company Comparison
3. Cash Flow Analysis
4. Revenue Forecast
5. Financial Anomalies
6. Financial Risk
7. Settings & Information

The semantic model connects to Snowflake analytical datasets.

The Desktop report is available locally. Power BI Service deployment and public report access remain unverified.

A known outstanding issue in the semantic model is a cyclic-reference error involving company performance, company comparison, and date-table relationships. This must be resolved and refreshed successfully before claiming a fully operational dashboard deployment.

## 10. AI and Retrieval-Augmented Generation

The AI application combines local inference, retrieval, and governed analytical access.

### Components

- Ollama
- Llama 3.2 3B
- ChromaDB
- FastAPI
- Streamlit
- Snowflake connector

The local vector collection is:

`aci_financial_knowledge`

The recorded vector-store document count is 1,338.

The retrieval architecture combines Snowflake analytical context with vector retrieval.

### Approved analytical access

The Snowflake connector restricts access to:

- `MART_COMPANY_PERFORMANCE`
- `MART_COMPANY_COMPARISON`
- `MART_REVENUE_FORECAST`
- `MART_CASH_FLOW_ANALYSIS`
- `MART_FINANCIAL_ANOMALIES`
- `MART_FINANCIAL_RISK_INDICATORS`

All six marts were successfully queried during a previous integration validation.

The AI assistant should distinguish supported facts from missing information. It must not invent values, imply unsupported calculations, or describe company-level financial data as AI-specific ROI.

Local model inference has been tested. Public application hosting has not been verified.

## 11. Testing and Validation

Previously recorded validation evidence:

| Area | Result |
|---|---|
| Python test suite | 41 passed |
| Python compilation | Passed |
| Dependency check | No broken requirements |
| dbt models | 20 models |
| dbt data tests | 72 |
| Latest integrated dbt build | 94 PASS, 0 WARN, 0 ERROR, 0 SKIP |
| Latest Airflow execution | 3 of 3 tasks successful |
| Ollama inference | Passed |
| Snowflake mart integration | Six approved marts queried |

The Python test count and previous integration checks are historical evidence. They were not all rerun as part of the 27 November Airflow execution.

## 12. Security and Governance

Security practices and required improvements include:

- Keep `.env` and `.env.airflow` outside version control.
- Do not expose Snowflake, AWS, database, or application secrets.
- Use private S3 storage.
- Use least-privilege IAM and Snowflake roles.
- Avoid running production services with administrative warehouse roles.
- Keep local development configuration separate from production secrets.
- Rotate any credential that may have been exposed.
- Apply access controls and audit logging before public deployment.

## 13. Known Limitations

1. Company-level SEC financial facts do not isolate AI-specific financial performance.
2. XBRL concept mapping and reporting calendars require careful interpretation.
3. CAPEX reporting-basis approval remains unresolved.
4. Revenue forecasts are analytical estimates, not reported results.
5. Power BI Service deployment remains unverified.
6. A Power BI semantic-model cyclic-reference issue remains outstanding.
7. The AI application is locally tested, not publicly hosted.
8. Production deployment requires additional security, monitoring, recovery, and operational validation.

## 14. Future Engineering Roadmap

Recommended next improvements:

- Resolve and regression-test Power BI semantic-model relationships.
- Deploy the application and warehouse integration in a controlled cloud environment.
- Replace development credentials and administrative roles with least-privilege identities.
- Add automated freshness and reconciliation checks.
- Add alerting for failed and delayed pipeline runs.
- Add data lineage and model documentation.
- Add CI checks for dbt and Python changes.
- Add repeatable deployment and rollback procedures.
- Establish operational cost and performance monitoring.
- Add independent review of financial accounting assumptions.

## 15. Conclusion

AI Capital Intelligence demonstrates an integrated financial data workflow from SEC extraction to governed Snowflake analytics and dbt transformations, with Airflow orchestration and Power BI and AI application interfaces.

The 27 November 2026 execution verifies that the SEC pipeline, output validation, and dbt build completed successfully within a single Airflow DAG run.

This project demonstrates practical data engineering, SQL transformation, data quality, orchestration, financial analytics, and applied AI. It should be understood as a validated portfolio implementation with specific cloud deployment and semantic-model work still outstanding.
