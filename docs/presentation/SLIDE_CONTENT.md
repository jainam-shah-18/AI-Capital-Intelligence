# AI Capital Intelligence
## Technical Project Presentation

### Slide 1 — Title
**AI Capital Intelligence**
End-to-End Financial Data Engineering and AI Analytics Platform

Technology: Python | AWS S3 | Snowflake | dbt | Airflow | Power BI | RAG

### Slide 2 — Executive Summary
- Financial intelligence platform built around SEC EDGAR company facts.
- Covers Amazon, Microsoft, Alphabet and Meta.
- Integrates ingestion, storage, transformation, orchestration, analytics and AI.
- Designed as a reproducible engineering workflow rather than a standalone dashboard.

### Slide 3 — Business Problem
- Financial facts are distributed across regulatory reporting.
- Fiscal periods and source conventions require normalization.
- Manual preparation is repetitive and difficult to monitor.
- Business users need trusted, accessible analytical outputs.

### Slide 4 — Solution
- Automated SEC data extraction.
- Python transformation and structured file generation.
- Separate S3 delivery and direct Snowflake loading.
- dbt-based analytics engineering and data quality.
- Airflow orchestration.
- Power BI and AI-assisted exploration.

### Slide 5 — System Architecture
Show `docs/architecture/system_architecture.mmd`.

Key design decision: S3 and Snowflake are separate delivery destinations from the Python pipeline.

### Slide 6 — Data Engineering
- SEC EDGAR Company Facts API.
- Python and Pandas processing.
- CSV and Parquet artifacts.
- Boto3 S3 uploads.
- Direct Snowflake loading through `write_pandas()`.

### Slide 7 — Warehouse and dbt
- Snowflake as the analytical warehouse.
- 2 staging models.
- 9 intermediate models.
- 9 analytical marts.
- 2 seeds and 2 sources.
- 72 dbt data tests.

### Slide 8 — Orchestration and Reliability
Airflow DAG:
1. `run_sec_pipeline`
2. `validate_pipeline_outputs`
3. `run_dbt_build`

Includes task dependencies, retries, execution timeouts and run logging.

### Slide 9 — Verified Execution Evidence
Latest verified manual Airflow run: 27 November 2026.

- Three DAG tasks succeeded.
- dbt build: 94 successful build steps.
- 72 data tests.
- Zero warnings.
- Zero errors.
- Zero skipped steps.

94 successful steps does not mean 94 tests.

### Slide 10 — Analytics and AI
Power BI:
- Seven report pages.
- Financial performance and comparisons.
- Forecasting, anomalies and risk analysis.
- Pipeline monitoring.

AI:
- Hybrid Snowflake and ChromaDB retrieval.
- Local Ollama inference.
- Answers grounded in approved marts and retrieved context.

### Slide 11 — Limitations and Production Readiness
- Financial data is company-wide, not AI-specific ROI.
- Forecasts are estimates.
- Risk and anomaly flags require human review.
- Power BI cyclic-reference issue remains unresolved.
- Public dashboard and AI hosting are not verified.
- Production security, deployment and alerting remain future work.

### Slide 12 — Conclusion and Roadmap
ACI demonstrates integrated data engineering and analytics capabilities.

Next steps:
- Resolve and validate Power BI model dependencies.
- Strengthen Snowflake security and credential management.
- Add production deployment automation and alerting.
- Host and independently test public application endpoints.
- Expand monitoring, recovery and operational documentation.

**Repository:** Add the verified public GitHub repository URL before external distribution.
