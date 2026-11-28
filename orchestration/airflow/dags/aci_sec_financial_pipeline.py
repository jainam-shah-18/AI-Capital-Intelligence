from datetime import timedelta
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pandas as pd
import pendulum

from airflow.sdk import dag, task, get_current_context

logger = logging.getLogger(__name__)

ACI_ROOT = Path("/opt/airflow/aci")
DATA_DIR = ACI_ROOT / "data" / "processed"
DBT_PROJECT = ACI_ROOT / "dbt"
DBT_PROFILES = Path("/opt/airflow/config/dbt")

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
    description="End-to-end SEC extraction, validation, Snowflake and dbt analytics pipeline",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 11, 7, tz="Asia/Kolkata"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=70),
    default_args={
        "owner": "aci",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["aci", "sec", "snowflake", "dbt", "financial-data"],
)
def aci_sec_financial_pipeline():

    @task(execution_timeout=timedelta(minutes=30))
    def run_sec_pipeline():
        import sys

        sys.path.insert(0, str(ACI_ROOT))

        from src.aci.pipeline import run

        context = get_current_context()
        airflow_run_id = context["dag_run"].run_id

        logger.info("Starting SEC pipeline: %s", airflow_run_id)
        run(run_id=airflow_run_id)
        logger.info("SEC pipeline completed: %s", airflow_run_id)

        return airflow_run_id

    @task(execution_timeout=timedelta(minutes=5))
    def validate_pipeline_outputs():
        csv_path = DATA_DIR / "financial_metrics.csv"
        parquet_path = DATA_DIR / "financial_metrics.parquet"

        if not csv_path.exists() or not parquet_path.exists():
            raise FileNotFoundError("CSV or Parquet pipeline output missing.")

        csv_df = pd.read_csv(csv_path)
        parquet_df = pd.read_parquet(parquet_path)

        if csv_df.empty or parquet_df.empty:
            raise ValueError("Pipeline output files must not be empty.")

        if len(csv_df) != len(parquet_df):
            raise ValueError("CSV and Parquet row counts do not match.")

        required_columns = {"ticker", "metric", "period_end"}
        missing = required_columns - set(csv_df.columns)

        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")

        actual_tickers = set(csv_df["ticker"].dropna().unique())
        actual_metrics = set(csv_df["metric"].dropna().unique())

        if actual_tickers != EXPECTED_TICKERS:
            raise ValueError(f"Unexpected companies: {sorted(actual_tickers)}")

        if actual_metrics != EXPECTED_METRICS:
            raise ValueError(f"Unexpected metrics: {sorted(actual_metrics)}")

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

    @task(execution_timeout=timedelta(minutes=30))
    def run_dbt_build():
        if not DBT_PROJECT.is_dir():
            raise FileNotFoundError(f"dbt project missing: {DBT_PROJECT}")

        if not (DBT_PROFILES / "profiles.yml").is_file():
            raise FileNotFoundError("Airflow dbt profiles.yml is missing.")

        context = get_current_context()
        run_id = context["dag_run"].run_id

        safe_run_id = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in run_id
        )

        log_dir = Path("/opt/airflow/logs/dbt") / safe_run_id
        log_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="aci-dbt-") as temp_dir:
            project_copy = Path(temp_dir) / "dbt"

            shutil.copytree(
                DBT_PROJECT,
                project_copy,
                ignore=shutil.ignore_patterns(
                    "target", "logs", "dbt_packages", ".git"
                ),
            )

            command = [
                "dbt",
                "build",
                "--project-dir", str(project_copy),
                "--profiles-dir", str(DBT_PROFILES),
                "--target", "dev",
                "--log-path", str(log_dir),
            ]

            logger.info("Starting dbt build for Airflow run %s", run_id)
            logger.info("Executing: dbt build --target dev")

            env = os.environ.copy()
            env["DBT_PROFILES_DIR"] = str(DBT_PROFILES)

            result = subprocess.run(
                command,
                cwd=str(project_copy),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout:
                logger.info("dbt output:\n%s", result.stdout)

            if result.stderr:
                logger.info("dbt stderr:\n%s", result.stderr)

            if result.returncode != 0:
                logger.error(
                    "dbt build failed with exit code %s",
                    result.returncode,
                )
                raise RuntimeError(
                    f"dbt build failed. Review task logs and {log_dir}"
                )

            logger.info("dbt build completed successfully.")
            return {"status": "SUCCESS", "run_id": run_id}

    sec_pipeline = run_sec_pipeline()
    output_validation = validate_pipeline_outputs()
    dbt_build = run_dbt_build()

    sec_pipeline >> output_validation >> dbt_build


aci_sec_financial_pipeline()
