
from datetime import timedelta
import logging
from pathlib import Path

import pandas as pd
import pendulum

from airflow.sdk import dag, task

logger = logging.getLogger(__name__)

ACI_ROOT = Path("/opt/airflow/aci")
DATA_DIR = ACI_ROOT / "data" / "processed"

EXPECTED_TICKERS = {"AMZN", "MSFT", "GOOGL", "META"}
EXPECTED_METRICS = {
    "capital_expenditure",
    "net_income",
    "operating_cash_flow",
    "operating_income",
    "revenue",
}


@dag(
    dag_id="aci_sec_financial_pipeline",
    description="Fetch SEC company facts, transform financial metrics and upload curated data to S3",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 11, 7, tz="Asia/Kolkata"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "aci",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["aci", "sec", "financial-data"],
)
def aci_sec_financial_pipeline():

    @task
    def run_sec_pipeline():
        import sys

        sys.path.insert(0, str(ACI_ROOT))

        from src.aci.pipeline import run

        logger.info("Starting ACI SEC financial data pipeline")
        run()
        logger.info("ACI SEC financial data pipeline completed")

    @task
    def validate_pipeline_outputs():
        csv_path = DATA_DIR / "financial_metrics.csv"
        parquet_path = DATA_DIR / "financial_metrics.parquet"

        if not csv_path.exists() or not parquet_path.exists():
            raise FileNotFoundError(
                "Expected CSV and Parquet pipeline outputs were not found."
            )

        csv_df = pd.read_csv(csv_path)
        parquet_df = pd.read_parquet(parquet_path)

        if csv_df.empty or parquet_df.empty:
            raise ValueError("Pipeline output files must not be empty.")

        if len(csv_df) != len(parquet_df):
            raise ValueError("CSV and Parquet row counts do not match.")

        required_columns = {"ticker", "metric", "period_end"}
        missing = required_columns - set(csv_df.columns)

        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        actual_tickers = set(csv_df["ticker"].dropna().unique())
        actual_metrics = set(csv_df["metric"].dropna().unique())

        if actual_tickers != EXPECTED_TICKERS:
            raise ValueError(
                f"Unexpected company set: {sorted(actual_tickers)}"
            )

        if actual_metrics != EXPECTED_METRICS:
            raise ValueError(
                f"Unexpected metric set: {sorted(actual_metrics)}"
            )

        logger.info(
            "Output validation passed: %s rows, %s companies, %s metrics",
            len(csv_df),
            len(actual_tickers),
            len(actual_metrics),
        )

        return {
            "rows": len(csv_df),
            "companies": len(actual_tickers),
            "metrics": len(actual_metrics),
        }

    pipeline_run = run_sec_pipeline()
    output_validation = validate_pipeline_outputs()

    pipeline_run >> output_validation


aci_sec_financial_pipeline()
