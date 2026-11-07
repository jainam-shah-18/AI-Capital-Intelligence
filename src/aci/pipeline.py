from pathlib import Path
import logging
import pandas as pd
from . import settings
from .sec_client import SECClient
from .transform import extract_financial_metrics
from .s3_storage import upload_file

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "sec"
PROCESSED_DIR = ROOT / "data" / "processed"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("aci.pipeline")

def run() -> None:
    client = SECClient(settings.SEC_USER_AGENT, settings.SEC_REQUEST_DELAY_SECONDS)
    frames = []
    raw_paths = []
    for ticker, company in settings.COMPANIES.items():
        logger.info("Fetching SEC Company Facts for %s (%s)", ticker, company["cik"])
        path = client.save_companyfacts(company["cik"], ticker, RAW_DIR)
        raw_paths.append((ticker, path))
        payload = __import__("json").loads(path.read_text(encoding="utf-8"))
        frame = extract_financial_metrics(payload, ticker, company["name"])
        logger.info("%s: extracted %s observations", ticker, len(frame))
        if not frame.empty:
            frames.append(frame)

    if not frames:
        raise RuntimeError("No financial observations were extracted. Check SEC response and supported XBRL tags.")

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["ticker", "period_end", "metric"])
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = PROCESSED_DIR / "financial_metrics.csv"
    parquet_path = PROCESSED_DIR / "financial_metrics.parquet"
    result.to_csv(csv_path, index=False)
    result.to_parquet(parquet_path, index=False)
    logger.info("Saved %s rows to %s and %s", len(result), csv_path, parquet_path)

    if settings.S3_BUCKET:
        for ticker, path in raw_paths:
            upload_file(path, settings.S3_BUCKET, f"raw/sec/companyfacts/{ticker}/{path.name}", settings.AWS_REGION)
        upload_file(csv_path, settings.S3_BUCKET, "curated/financial_metrics/financial_metrics.csv", settings.AWS_REGION)
        upload_file(parquet_path, settings.S3_BUCKET, "curated/financial_metrics/financial_metrics.parquet", settings.AWS_REGION)
        logger.info("Uploaded raw and curated files to S3 bucket %s", settings.S3_BUCKET)

    if settings.SNOWFLAKE_ACCOUNT and settings.SNOWFLAKE_USER and settings.SNOWFLAKE_PASSWORD:
        from .snowflake_storage import load_metrics
        count = load_metrics(result)
        logger.info("Loaded %s rows into Snowflake FINANCIAL_METRICS", count)

    print("\nDay 1 pipeline completed.")
    print(f"Companies: {result['ticker'].nunique()}")
    print(f"Rows: {len(result):,}")
    print(f"Metrics: {', '.join(sorted(result['metric'].unique()))}")
    print(f"CSV: {csv_path}")
    print(f"Parquet: {parquet_path}")

if __name__ == "__main__":
    run()
