# AI Capital Intelligence

An end-to-end financial intelligence platform that transforms SEC filings into governed financial analytics, company comparisons, anomaly detection, forecasts and AI-assisted explanations.

## Companies
Amazon (AMZN) | Microsoft (MSFT) | Alphabet (GOOGL) | Meta (META)

## Architecture
SEC EDGAR API -> Python ingestion -> AWS S3 -> Snowflake RAW/STAGING -> dbt analytics -> Power BI.

Apache Airflow orchestrates ingestion and output validation. The AI application uses local LLM inference and vector retrieval.

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
The Python pipeline extracts and normalizes SEC financial observations and writes CSV and Parquet outputs. It supports S3 uploads and Snowflake loading.

Snowflake layers:
- RAW: ingested financial metrics
- STAGING: SEC observations and eligibility filtering
- ANALYTICS: analytical source views
- DBT_DEV: transformed analytical models

## dbt Analytics
- 18 dbt models
- 2 seeds
- 1 source
- 61 data tests

Capabilities include canonical metric selection, filing evidence validation, quarterly period alignment, cash-flow derivation, company comparison, revenue forecasting, anomaly detection and financial risk indicators.

Latest validation: 18/18 models built successfully; 61/61 tests passed.

## Cash Flow Accounting
Quarterly cash-flow derivation supports Q2 = H1 - Q1, Q3 = nine-month cumulative - H1, and Q4 = annual cumulative - nine-month cumulative.

Reported quarterly values are preferred when available.

Important: CAPEX reporting-basis approval remains unresolved. FREE_CASH_FLOW is intentionally NULL. FREE_CASH_FLOW_CANDIDATE is an arithmetic candidate and must not be presented as approved official free cash flow.

## Power BI
The repository includes AI_Capital_Intelligence.pbix with six interactive dashboard pages covering financial performance, company comparison, cash flow, forecasting, anomalies and risk.

## AI Financial Intelligence
The local AI application includes:
- Ollama with Llama 3.2 3B
- ChromaDB retrieval
- Financial assistant and retrieval modules
- FastAPI service
- Streamlit interface

Ollama inference has been tested successfully. Direct AI-to-Snowflake querying requires valid AI-specific Snowflake authentication, which is not currently configured. The main Python, Snowflake and dbt pipeline is operational independently.

## Airflow
DAG: aci_sec_financial_pipeline

Tasks:
- run_sec_pipeline
- validate_pipeline_outputs

The DAG is registered, unpaused and its manual execution has succeeded. dbt runs and tests are executed separately, not as tasks in this DAG.

## Validation Results
- Python tests: 38 passed
- dbt models: 18 passed
- dbt tests: 61 passed
- Python compilation: passed
- Dependency check: no broken requirements
- Ollama inference: passed
- Airflow DAG: registered and unpaused
- SEC pipeline: 4,529 observations extracted and loaded

## Running the Project

Python tests:
    python -m pytest -q

Python ingestion:
    python -m src.aci.pipeline

dbt commands (from the dbt directory):
    dbt debug
    dbt run
    dbt test

Airflow (from the project root):
    docker compose --env-file .\.env --env-file .\orchestration\airflow\.env.airflow -f .\orchestration\airflow\docker-compose.yaml up -d --build

Configure local credentials and dbt profiles before running cloud-connected components. Never commit secrets or environment files.

## Security and Limitations
- Keep credentials, tokens and private keys out of Git.
- Keep S3 buckets private and use least-privilege permissions.
- Do not commit virtual environments, generated vector stores or temporary exports.
- SEC XBRL concepts and reporting practices can differ between companies.
- Missing financial observations are not fabricated.
- Forecasts are analytical estimates, not reported results.
- This platform is for financial analytics and demonstration, not investment advice.

## License
See LICENSE.
