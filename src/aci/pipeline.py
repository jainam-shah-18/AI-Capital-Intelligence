
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import json
import logging

import pandas as pd

from . import settings
from .sec_client import SECClient
from .transform import extract_financial_metrics
from .s3_storage import upload_file
from .monitoring import record_event


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "sec"
PROCESSED_DIR = ROOT / "data" / "processed"

PIPELINE_NAME = "aci_sec_financial_pipeline"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("aci.pipeline")


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _record_event_safely(**kwargs):
    """Record monitoring events without interrupting the data pipeline."""
    try:
        record_event(**kwargs)
    except Exception:
        logger.exception(
            "Pipeline monitoring failed for component %s. "
            "The data pipeline will continue.",
            kwargs.get("component", "UNKNOWN"),
        )


def _start(run_id, component, source=None, target=None):
    started = _now()

    _record_event_safely(
        run_id=run_id,
        pipeline_name=PIPELINE_NAME,
        component=component,
        status="RUNNING",
        started_at=started,
        source_name=source,
        target_name=target,
    )

    return started


def _finish(
    run_id,
    component,
    started,
    status,
    rows_extracted=None,
    rows_loaded=None,
    source=None,
    target=None,
    error=None,
):
    finished = _now()
    duration = (finished - started).total_seconds()

    _record_event_safely(
        run_id=run_id,
        pipeline_name=PIPELINE_NAME,
        component=component,
        status=status,
        started_at=started,
        finished_at=finished,
        duration_seconds=duration,
        rows_extracted=rows_extracted,
        rows_loaded=rows_loaded,
        source_name=source,
        target_name=target,
        error_message=str(error)[:4000] if error else None,
    )


def run(run_id=None) -> None:
    run_id = run_id or str(uuid4())
    pipeline_started = _start(run_id, "PIPELINE")

    try:
        # 1. SEC extraction
        extraction_started = _start(
            run_id,
            "SEC_EXTRACTION",
            source="SEC EDGAR Company Facts API",
            target="data/raw/sec",
        )

        try:
            client = SECClient(
                settings.SEC_USER_AGENT,
                settings.SEC_REQUEST_DELAY_SECONDS
            )

            frames = []
            raw_paths = []

            for ticker, company in settings.COMPANIES.items():
                logger.info(
                    "Fetching SEC Company Facts for %s (%s)",
                    ticker,
                    company["cik"]
                )

                path = client.save_companyfacts(
                    company["cik"],
                    ticker,
                    RAW_DIR
                )
                raw_paths.append((ticker, path))

                payload = json.loads(
                    path.read_text(encoding="utf-8")
                )

                frame = extract_financial_metrics(
                    payload,
                    ticker,
                    company["name"]
                )

                logger.info(
                    "%s: extracted %s observations",
                    ticker,
                    len(frame)
                )

                if not frame.empty:
                    frames.append(frame)

            if not frames:
                raise RuntimeError(
                    "No financial observations were extracted."
                )

            result = pd.concat(frames, ignore_index=True)
            result = result.sort_values(
                ["ticker", "period_end", "metric"]
            )

            _finish(
                run_id,
                "SEC_EXTRACTION",
                extraction_started,
                "SUCCESS",
                rows_extracted=len(result),
                source="SEC EDGAR Company Facts API",
                target="data/raw/sec",
            )

        except Exception as exc:
            _finish(
                run_id,
                "SEC_EXTRACTION",
                extraction_started,
                "FAILED",
                source="SEC EDGAR Company Facts API",
                target="data/raw/sec",
                error=exc,
            )
            raise

        # 2. Local transformation and output files
        transform_started = _start(
            run_id,
            "LOCAL_TRANSFORM",
            source="SEC extracted observations",
            target="data/processed/financial_metrics",
        )

        try:
            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

            csv_path = PROCESSED_DIR / "financial_metrics.csv"
            parquet_path = PROCESSED_DIR / "financial_metrics.parquet"

            result.to_csv(csv_path, index=False)
            result.to_parquet(parquet_path, index=False)

            logger.info(
                "Saved %s rows to %s and %s",
                len(result),
                csv_path,
                parquet_path
            )

            _finish(
                run_id,
                "LOCAL_TRANSFORM",
                transform_started,
                "SUCCESS",
                rows_extracted=len(result),
                rows_loaded=len(result),
                source="SEC extracted observations",
                target="CSV and Parquet files",
            )

        except Exception as exc:
            _finish(
                run_id,
                "LOCAL_TRANSFORM",
                transform_started,
                "FAILED",
                rows_extracted=len(result),
                source="SEC extracted observations",
                target="CSV and Parquet files",
                error=exc,
            )
            raise

        # 3. S3 delivery
        if settings.S3_BUCKET:
            s3_started = _start(
                run_id,
                "S3_DELIVERY",
                source="Local raw and curated files",
                target=f"s3://{settings.S3_BUCKET}/",
            )

            try:
                for ticker, path in raw_paths:
                    upload_file(
                        path,
                        settings.S3_BUCKET,
                        f"raw/sec/companyfacts/{ticker}/{path.name}",
                        settings.AWS_REGION,
                    )

                upload_file(
                    csv_path,
                    settings.S3_BUCKET,
                    "curated/financial_metrics/financial_metrics.csv",
                    settings.AWS_REGION,
                )

                upload_file(
                    parquet_path,
                    settings.S3_BUCKET,
                    "curated/financial_metrics/financial_metrics.parquet",
                    settings.AWS_REGION,
                )

                _finish(
                    run_id,
                    "S3_DELIVERY",
                    s3_started,
                    "SUCCESS",
                    rows_extracted=len(result),
                    rows_loaded=len(result),
                    source="Local raw and curated files",
                    target=f"s3://{settings.S3_BUCKET}/",
                )

                logger.info(
                    "Uploaded raw and curated files to S3 bucket %s",
                    settings.S3_BUCKET
                )

            except Exception as exc:
                _finish(
                    run_id,
                    "S3_DELIVERY",
                    s3_started,
                    "FAILED",
                    rows_extracted=len(result),
                    source="Local raw and curated files",
                    target=f"s3://{settings.S3_BUCKET}/",
                    error=exc,
                )
                raise
        else:
            _finish(
                run_id,
                "S3_DELIVERY",
                _now(),
                "NOT_CONFIGURED",
                source="Local raw and curated files",
                target="S3",
            )

        # 4. Snowflake financial data delivery
        if (
            settings.SNOWFLAKE_ACCOUNT
            and settings.SNOWFLAKE_USER
            and settings.SNOWFLAKE_PASSWORD
        ):
            snowflake_started = _start(
                run_id,
                "SNOWFLAKE_LOAD",
                source="Local financial metrics DataFrame",
                target=(
                    f"{settings.SNOWFLAKE_DATABASE}."
                    f"{settings.SNOWFLAKE_SCHEMA}.FINANCIAL_METRICS"
                ),
            )

            try:
                from .snowflake_storage import load_metrics

                count = load_metrics(result)

                _finish(
                    run_id,
                    "SNOWFLAKE_LOAD",
                    snowflake_started,
                    "SUCCESS",
                    rows_extracted=len(result),
                    rows_loaded=count,
                    source="Local financial metrics DataFrame",
                    target=(
                        f"{settings.SNOWFLAKE_DATABASE}."
                        f"{settings.SNOWFLAKE_SCHEMA}.FINANCIAL_METRICS"
                    ),
                )

                logger.info(
                    "Loaded %s rows into Snowflake FINANCIAL_METRICS",
                    count
                )

            except Exception as exc:
                _finish(
                    run_id,
                    "SNOWFLAKE_LOAD",
                    snowflake_started,
                    "FAILED",
                    rows_extracted=len(result),
                    source="Local financial metrics DataFrame",
                    target="FINANCIAL_METRICS",
                    error=exc,
                )
                raise
        else:
            _finish(
                run_id,
                "SNOWFLAKE_LOAD",
                _now(),
                "NOT_CONFIGURED",
                source="Local financial metrics DataFrame",
                target="Snowflake FINANCIAL_METRICS",
            )

        _finish(
            run_id,
            "PIPELINE",
            pipeline_started,
            "SUCCESS",
            rows_extracted=len(result),
            rows_loaded=len(result),
            source="SEC EDGAR Company Facts API",
            target="Local files, S3 and Snowflake",
        )

        print("\nDay 1 pipeline completed.")
        print(f"Run ID: {run_id}")
        print(f"Companies: {result['ticker'].nunique()}")
        print(f"Rows: {len(result):,}")
        print(f"Metrics: {', '.join(sorted(result['metric'].unique()))}")
        print(f"CSV: {csv_path}")
        print(f"Parquet: {parquet_path}")

    except Exception as exc:
        _finish(
            run_id,
            "PIPELINE",
            pipeline_started,
            "FAILED",
            error=exc,
            source="SEC EDGAR Company Facts API",
            target="ACI pipeline outputs",
        )
        raise


if __name__ == "__main__":
    run()
