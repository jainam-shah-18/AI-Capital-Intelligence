# AI Capital Intelligence

An end-to-end financial intelligence platform that transforms SEC filings into governed financial analytics, company comparisons, anomaly detection, revenue forecasts, and AI-assisted explanations.

## Companies

Amazon (AMZN) | Microsoft (MSFT) | Alphabet (GOOGL) | Meta (META)

## Architecture

SEC EDGAR API -> Python ingestion -> AWS S3 -> Snowflake RAW/STAGING -> dbt analytics -> Power BI.

Apache Airflow orchestrates ingestion and output validation. The AI application combines local LLM inference, vector retrieval, and controlled access to Snowflake analytical marts.

## Technology Stack

- Python, Pandas, NumPy, Pytest
- SEC EDGAR Company Facts API
- AWS S3
- Snowflake
- dbt Core
- Apache Airflow and Docker
- GitHub Actions
- Power BI
- Ollama, Llama 3.2, ChromaDB
- FastAPI and Streamlit

## Data Engineering

The Python pipeline extracts and normalizes SEC financial observations and produces CSV and Parquet outputs. It supports S3 uploads and Snowflake loading.

Snowflake layers:
- RAW: ingested financial metrics
- STAGING: SEC observations and eligibility filtering
- ANALYTICS: analytical source views
- DBT_DEV: transformed analytical models

The latest pipeline execution extracted and loaded 4,529 observations across the four companies.

## dbt Analytics

- 18 dbt models
- 2 seeds
- 1 source
- 61 data tests

Capabilities include canonical metric selection, filing evidence validation, quarterly period alignment, cash-flow derivation, company comparison, revenue forecasting, anomaly detection, and financial risk indicators.

Latest validation:
- 18/18 models built successfully
- 61/61 data tests passed

## Cash Flow Accounting

Quarterly cash-flow derivation supports:
- Q2 = H1 - Q1
- Q3 = nine-month cumulative - H1
- Q4 = annual cumulative - nine-month cumulative

Reported quarterly values are preferred when available.

Important: CAPEX reporting-basis approval remains unresolved. `FREE_CASH_FLOW` is intentionally NULL where the basis is not approved. `FREE_CASH_FLOW_CANDIDATE` is an arithmetic candidate and must not be presented as approved official free cash flow.

## Power BI

The repository includes `AI_Capital_Intelligence.pbix`, containing seven report pages: six analytical dashboard pages covering financial performance, company comparison, cash flow, forecasting, anomalies, and risk, plus a Settings & Information page with dashboard navigation.

The PBIX has been saved locally and committed to GitHub. Power BI Service accessibility and cloud deployment have not been verified because the available personal Microsoft account could not complete Fabric onboarding.

## AI Financial Intelligence

The local AI application includes:
- Ollama with Llama 3.2 3B
- ChromaDB retrieval
- Financial assistant and retrieval modules
- FastAPI service
- Streamlit interface
- Snowflake analytical mart integration

Ollama inference has been tested successfully.

The Snowflake connector uses local environment configuration and restricts queries to six approved analytical marts:
- `MART_COMPANY_PERFORMANCE`
- `MART_COMPANY_COMPARISON`
- `MART_REVENUE_FORECAST`
- `MART_CASH_FLOW_ANALYSIS`
- `MART_FINANCIAL_ANOMALIES`
- `MART_FINANCIAL_RISK_INDICATORS`

All six marts were successfully queried during integration validation. Credentials must be configured locally and must never be committed to the repository.

## Airflow

DAG: `aci_sec_financial_pipeline`

Tasks:
- `run_sec_pipeline`
- `validate_pipeline_outputs`

The DAG is registered, unpaused, and its manual execution has succeeded. dbt runs and tests are executed separately, not as tasks in this DAG.

## Validation Results

- Python tests: 38 passed
- dbt models: 18 built successfully
- dbt tests: 61 passed, 0 warnings, 0 errors
- Python compilation: passed
- Dependency check: no broken requirements
- Ollama inference: passed
- Snowflake integration: all six approved marts queried successfully
- Airflow DAG: registered and unpaused; manual execution succeeded
- SEC pipeline: 4,529 observations extracted and loaded

## Running the Project

Run Python tests from the project root:

    python -m pytest -q

Run Python ingestion from the project root:

    python -m src.aci.pipeline

Run dbt commands from the dbt directory:

    dbt debug
    dbt run
    dbt test

Start Airflow from the project root:

    docker compose --env-file .\.env --env-file .\orchestration\airflow\.env.airflow -f .\orchestration\airflow\docker-compose.yaml up -d --build

Configure local credentials and dbt profiles before running cloud-connected components. Never commit secrets or environment files.

## Security and Limitations

- Keep credentials, tokens, and private keys out of Git.
- Keep S3 buckets private and use least-privilege permissions.
- Do not commit virtual environments, generated vector stores, or temporary exports.
- SEC XBRL concepts and reporting practices can differ between companies.
- Missing financial observations are not fabricated.
- Official free cash flow remains subject to CAPEX reporting-basis approval.
- Forecasts are analytical estimates, not reported results.
- Power BI Service cloud deployment remains unverified; the local PBIX is included in the repository.
- This platform is for financial analytics and demonstration, not investment advice.

## License

See LICENSE.
