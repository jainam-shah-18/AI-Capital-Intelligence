# AI Capital Intelligence

An end-to-end financial intelligence platform that transforms public SEC filings into governed financial analytics, company comparisons, anomaly indicators and AI-assisted explanations.

The platform combines Python ingestion, AWS S3, Snowflake, dbt Core, Apache Airflow, Power BI and a local LLM/RAG application.

## Project Overview

AI Capital Intelligence analyzes publicly reported financial information for:

- Amazon (AMZN)
- Microsoft (MSFT)
- Alphabet (GOOGL)
- Meta (META)

The platform is designed to support financial analysis through traceable source data, canonical metric selection, reporting-period alignment, data-quality validation and interactive dashboards.

**Important:** SEC company facts represent company-wide financial reporting. They do not isolate AI-specific revenue, expenditure or return on investment.

## Architecture

```text
SEC EDGAR Company Facts API
             |
             v
     Python Data Pipeline
             |
       +-----+------+
       |            |
       v            v
    AWS S3       Snowflake
  Raw/Curated       |
                    v
              STAGING / RAW
                    |
                    v
                dbt Core
                    |
       +------------+------------+
       |            |            |
       v            v            v
   Canonical     Financial    Analytical
    Metrics       Periods      Marts
       |            |            |
       +------------+------------+
                    |
                    v
                Power BI
              Six Dashboards

       AI / RAG Application
       Streamlit + FastAPI
       Ollama + ChromaDB
                    |
                    v
          Financial Data Retrieval
          and AI-assisted Explanations

       Apache Airflow
       Pipeline Orchestration
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Programming | Python, SQL |
| Data source | SEC EDGAR Company Facts API |
| Data processing | Pandas, NumPy |
| Cloud storage | AWS S3 |
| Data warehouse | Snowflake |
| Transformation | dbt Core |
| Orchestration | Apache Airflow |
| Infrastructure | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Business intelligence | Power BI |
| AI / LLM | Ollama, Llama 3.2 |
| Retrieval | ChromaDB |
| API | FastAPI |
| Application | Streamlit |
| Testing | Pytest, dbt tests |

## Data Engineering Pipeline

### 1. Data ingestion

Python retrieves SEC Company Facts data for four publicly traded companies.

The pipeline supports:
- SEC JSON ingestion
- Financial metric extraction
- Data normalization
- CSV and Parquet outputs
- AWS S3 uploads
- Snowflake loading

### 2. Snowflake data warehouse

The warehouse separates data into functional schemas:

- `RAW` — ingested financial metrics
- `STAGING` — SEC observations and eligibility filtering
- `ANALYTICS` — analytical source views
- `DBT_DEV` — transformed dbt models

### 3. dbt transformation

The dbt project implements staging, intermediate and mart layers.

Key transformations include:
- Financial observation classification
- Canonical financial metric selection
- Filing evidence and reporting-period validation
- Quarterly financial period alignment
- Quarterly cash-flow derivation
- Financial performance analysis
- Company comparison
- Revenue forecasting
- Financial anomaly detection
- Financial risk indicators

**Current validation results:**
- 18 dbt models
- 2 seeds
- 61 data tests
- 1 declared source
- 61 tests passed in the latest full test run

### 4. Cash-flow accounting controls

The cash-flow mart distinguishes reported quarterly values from derived quarterly candidates.

Quarterly derivation supports:
- Q2 = first-half cumulative value minus Q1
- Q3 = nine-month cumulative value minus first-half cumulative value
- Q4 = annual value minus nine-month cumulative value

Free cash flow candidates are exposed separately from approved free cash flow.

**Accounting limitation:** The current CAPEX reporting-basis review is unresolved. Consequently, `FREE_CASH_FLOW` remains NULL, and `FREE_CASH_FLOW_CANDIDATE` must not be interpreted as approved official FCF.

## Power BI Dashboards

The repository includes `AI_Capital_Intelligence.pbix`, containing six interactive dashboard pages.

The dashboards use Snowflake/dbt analytical outputs for financial monitoring and comparison.

The dashboard layer supports financial performance analysis, company comparisons, cash-flow analysis, forecasts, anomalies and risk-related insights.

## AI Financial Intelligence

The AI layer provides local LLM-assisted explanations grounded in retrieved financial data.

Components include:
- Ollama for local LLM inference
- Llama 3.2 3B as the configured chat model
- ChromaDB for vector retrieval
- Python-based financial retrieval and assistant modules
- FastAPI endpoints
- Streamlit application

The AI model is instructed to use supplied financial context, distinguish reported results from forecasts, avoid inventing financial figures and leave database calculations to the analytical layer.

**Authentication status:** Local Ollama inference has been tested successfully. Direct AI-to-Snowflake querying requires valid AI-specific Snowflake authentication, which must be configured securely before that integration can be used.

## Airflow Orchestration

Apache Airflow runs the SEC ingestion and pipeline-output validation DAG.

DAG ID:

`aci_sec_financial_pipeline`

The current DAG includes:
- `run_sec_pipeline`
- `validate_pipeline_outputs`

A manual DAG execution completed successfully.

dbt transformations and tests have been executed and validated separately; they are not currently tasks in this Airflow DAG.

## Running the Project

### Prerequisites

- Windows 10/11
- Python 3.10+
- Git
- Docker Desktop
- Snowflake account
- AWS account for S3 functionality
- Ollama for local AI functionality

### 1. Clone the repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd ai-capital-intelligence-day1
```

### 2. Create the Python environment

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Configure the required values locally. Never commit `.env`, Airflow environment files, passwords, tokens or private keys.

### 4. Run the ingestion pipeline

```powershell
python -m src.aci.pipeline
```

### 5. Run Python tests

```powershell
pytest -q
```

### 6. Run dbt

```powershell
cd dbt
dbt debug
dbt run
dbt test
```

Configure the dbt profile and Snowflake credentials before execution.

### 7. Start Airflow

From the project root:

```powershell
docker compose `
  --env-file .\.env `
  --env-file .\orchestration\airflow\.env.airflow `
  -f .\orchestration\airflow\docker-compose.yaml up -d --build
```

### 8. Run the AI application

Configure Ollama and the AI-specific Snowflake authentication before using the complete financial Q&A workflow.

The configured local chat model is:

`llama3.2:3b`

The embedding model installed locally is:

`nomic-embed-text`

## Repository Structure

```text
ai-capital-intelligence-day1/
|
+-- .github/
+-- data/
+-- dbt/
|   +-- models/
|   |   +-- staging/
|   |   +-- intermediate/
|   |   +-- marts/
|   +-- seeds/
|   +-- tests/
|
+-- orchestration/
|   +-- airflow/
|       +-- dags/
|
+-- scripts/
+-- src/
|   +-- aci/
|       +-- pipeline.py
|       +-- ai_api.py
|       +-- ai_app.py
|       +-- ai_assistant.py
|       +-- ai_chat.py
|       +-- ai_indexer.py
|       +-- ai_llm.py
|       +-- ai_rag.py
|       +-- ai_retrieval.py
|       +-- ai_snowflake.py
|
+-- tests/
+-- warehouse/
+-- AI_Capital_Intelligence.pbix
+-- requirements.txt
+-- README.md
```

## Security

- Keep all environment files out of version control.
- Never commit Snowflake passwords, programmatic access tokens or private keys.
- Keep AWS S3 buckets private with Block Public Access enabled.
- Use least-privilege cloud permissions.
- Avoid committing generated vector databases, local virtual environments or temporary exports.
- Rotate any credential that may have been exposed.

## Data Interpretation and Limitations

- Financial metrics originate from SEC company filings.
- Reporting practices and XBRL concepts may differ between companies.
- Missing observations are not fabricated.
- Quarterly cash-flow derivations require compatible reporting periods and concepts.
- Free cash flow candidates are not approved official FCF until the relevant CAPEX reporting basis is validated.
- Forecasts are analytical estimates, not reported financial results.
- The platform is intended for financial analytics and demonstration, not investment advice.

## License

See [LICENSE](LICENSE).
