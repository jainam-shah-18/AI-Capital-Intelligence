# AI Capital Intelligence — Technical Interview Guide

## 1. 60-Second Project Explanation

I built AI Capital Intelligence, an end-to-end financial data engineering and analytics platform using SEC EDGAR company financial data.

The pipeline extracts financial observations for Amazon, Microsoft, Alphabet, and Meta using Python, stores structured data, and loads it into Snowflake. I use dbt to build staging, intermediate, and analytical models, with automated data quality tests. Apache Airflow orchestrates ingestion, validation, and dbt execution.

Power BI provides financial dashboards, while a local RAG-based AI assistant supports natural-language exploration using approved analytical data and indexed financial knowledge.

The goal was to build an integrated, testable analytics platform rather than an isolated dashboard or notebook.

## 2. Architecture Questions

### Why did you use Snowflake?

Snowflake provides a cloud data warehouse for structured financial observations and analytical workloads. It separates ingestion from downstream transformations and reporting.

### Why dbt?

dbt makes SQL transformations modular, version-controlled, testable, and easier to maintain. I separated staging, intermediate logic, and analytical marts.

### Why Apache Airflow?

Airflow coordinates the pipeline, defines task dependencies, handles retries, and records execution status. The DAG has three main tasks:

1. Run the SEC pipeline.
2. Validate pipeline outputs.
3. Execute the dbt build.

### Why S3?

S3 provides object storage for pipeline artifacts and supports separation between ingestion outputs and warehouse processing.

### Why Power BI?

Power BI provides a business-facing layer for exploring financial performance, comparisons, forecasts, anomalies, and risk indicators.

## 3. Data Quality Questions

### How do you validate the data?

I use Python-level pipeline validation and dbt data tests. The latest verified dbt build completed with 94 successful build steps, including 72 data tests, with zero warnings or errors.

### Does 94 PASS mean 94 tests?

No. It represents all successful dbt build steps. The build contained 72 data tests, alongside seeds and model operations.

### How do you handle missing values?

Missing values must not automatically be interpreted as zero. The transformation logic preserves unavailable or unapproved values rather than manufacturing financial results.

### What is the free cash flow limitation?

The project does not approve an unsupported free cash flow calculation. `FREE_CASH_FLOW` remains NULL where its calculation basis is not approved, and `FREE_CASH_FLOW_CANDIDATE` is not represented as an approved measure.

## 4. Analytics Questions

### What does the revenue forecast represent?

It is a model-generated estimate based on historical financial observations. It must be evaluated against actual results and is not a reported company figure.

### Are anomaly flags proof of financial misconduct?

No. They identify observations that may deserve investigation. A flag requires context and human review.

### Does this project calculate AI-specific ROI?

No. The SEC data represents company-wide financial reporting. It cannot independently identify AI-specific revenue, expenditure, or returns.

## 5. AI and RAG Questions

### Why use RAG?

Retrieval-augmented generation gives the assistant relevant indexed context before generating a response. This can improve grounding and make financial exploration more useful.

### What is the role of ChromaDB?

ChromaDB stores and retrieves vector-indexed financial knowledge for semantic retrieval.

### Why combine Snowflake and ChromaDB?

Snowflake provides structured analytical data, while ChromaDB supports semantic retrieval from indexed knowledge. The application combines these retrieval paths.

### How do you reduce hallucinations?

The application is designed to use approved marts and retrieved context rather than inventing financial values. Answers should preserve source context and distinguish reported figures from estimates.

## 6. Operational Questions

### What is the latest verified integrated run?

The manual Airflow run on 27 November 2026 completed all three DAG tasks successfully. Its dbt build completed with 94 successful steps, zero warnings, zero errors, and zero skipped steps.

### Is the platform production deployed?

The integrated workflow has been validated locally using Docker, Airflow, Snowflake, and dbt. Public deployment of the dashboard and AI application has not been verified.

### What would you improve before production?

- Resolve the Power BI semantic-model cyclic-reference issue.
- Introduce least-privilege Snowflake service roles.
- Rotate and centrally manage credentials.
- Add alerting and incident runbooks.
- Automate deployment and environment promotion.
- Add backup and recovery testing.
- Deploy and independently test hosted application endpoints.

## 7. Honest Lessons Learned

- Financial data requires careful handling of fiscal periods, units, and source definitions.
- A successful pipeline does not automatically guarantee business correctness.
- Data tests and observability should be designed into the system.
- AI answers need grounded retrieval and clear boundaries.
- Local integration is not the same as production deployment.
- Documentation and reproducibility are part of engineering quality.

## 8. Interview Demonstration Sequence

1. Explain the business problem and architecture.
2. Show the Airflow DAG and latest successful run.
3. Show dbt layers and data quality results.
4. Demonstrate Snowflake analytical marts.
5. Walk through the Power BI report and explain its current model limitation.
6. Demonstrate the local AI/RAG workflow.
7. Explain security, deployment boundaries, and next steps.
