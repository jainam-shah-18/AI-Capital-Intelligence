# AI Capital Intelligence

An industry-style financial data platform prototype that ingests public SEC company facts, normalizes selected financial metrics, stores raw and curated data, and optionally publishes to AWS S3 and Snowflake.

## Day 1 scope

- Real source: SEC EDGAR Company Facts API (no API key required).
- Companies: Amazon (AMZN), Microsoft (MSFT), Alphabet (GOOGL), Meta (META).
- Raw layer: downloaded SEC JSON snapshots.
- Curated layer: normalized quarterly and annual financial metrics in CSV and Parquet.
- Optional cloud sinks: private AWS S3 bucket and Snowflake table.
- Tests: offline transformation tests with synthetic fixtures.

> Financial data is reported company data, not an estimate of AI-specific revenue or AI-specific return on investment. SEC company facts generally describe company-wide financial metrics. We will not claim that they isolate AI infrastructure returns.

## Architecture

SEC EDGAR Company Facts -> Python ingestion -> local raw/curated files -> AWS S3 (optional) -> Snowflake (optional).

Airflow, PySpark, dbt, ML, RAG, API and BI layers are planned for subsequent project days. They are not represented as completed in this starter.

## Requirements

- Windows 10/11
- Python 3.11 or 3.12
- Git
- AWS CLI v2 (only if using S3)
- Snowflake account (optional on Day 1)

## 1. Create the environment (PowerShell)

```powershell
cd path\to\ai-capital-intelligence
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Configure SEC identification

Open `.env` and set `SEC_USER_AGENT` to identify your application and a contact email, for example:

`SEC_USER_AGENT=AI-Capital-Intelligence contact your.email@example.com`

Use your own email address. Do not commit `.env`.

The SEC's public data APIs do not require API keys. Automated access must follow SEC fair-access guidance and identify the requesting application.

## 3. Run the real-data pipeline locally

```powershell
python -m src.aci.pipeline
```

Expected outputs:
- `data/raw/sec/AMZN_companyfacts.json` (and other companies)
- `data/processed/financial_metrics.csv`
- `data/processed/financial_metrics.parquet`

The pipeline makes one Company Facts request per company and pauses briefly between requests.

## 4. Run tests

```powershell
pytest -q
```

Tests use synthetic data and do not call SEC or cloud services.

## 5. Optional AWS S3 upload

Configure AWS credentials using an IAM identity with least-privilege access to the target bucket. Prefer AWS IAM Identity Center / `aws configure sso` where available; do not put AWS access keys in source code.

```powershell
aws configure
aws sts get-caller-identity
```

Create a private bucket in your preferred region, keep Block Public Access enabled, enable default encryption, and set a lifecycle rule if retaining repeated raw snapshots. Put the bucket name in `.env` as `S3_BUCKET`.

Then run:
```powershell
python -m src.aci.pipeline
```

When `S3_BUCKET` is set, raw JSON and curated files are uploaded to:
- `raw/sec/companyfacts/<TICKER>/...`
- `curated/financial_metrics/...`

## 6. Optional Snowflake setup

Run `warehouse/schema.sql` in a Snowflake worksheet using a role allowed to create a database, schema, warehouse and table. The warehouse is X-Small with auto-suspend after 60 seconds and auto-resume enabled. It is created suspended. Start it only when loading/querying data and monitor remaining trial credits.

Set the Snowflake variables in `.env`, then run:
```powershell
python -m src.aci.pipeline
```

The pipeline loads curated rows into `FINANCIAL_METRICS` when Snowflake settings are supplied.

## Data interpretation

- Amounts are normalized to USD.
- Quarterly values use reported facts with approximately 70–110 day durations.
- Annual values use approximately 330–380 day durations.
- Some companies/tags may not expose every metric for every period. Missing values are omitted rather than fabricated.
- Free cash flow is calculated as operating cash flow minus capital expenditure (capital expenditure normalized as a positive outflow).
- Financial statement tags and reporting practices can differ. Validate values against source filings before making investment conclusions.

## Security and cost controls

- Never commit `.env`, AWS credentials, Snowflake passwords, tokens or private keys.
- Keep the S3 bucket private and Block Public Access enabled.
- Do not enable public access or create broad IAM administrator keys for this project.
- Keep the Snowflake warehouse X-Small and auto-suspend enabled; stop it when not in use.
- Check AWS and Snowflake billing/credit dashboards regularly. Free-tier eligibility and trial credits vary by account and region.

## Repository status

This is the Day 1 starter scaffold. Cloud services are not connected until you configure credentials and run the relevant setup steps.
