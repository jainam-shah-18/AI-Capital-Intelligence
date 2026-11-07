
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.aci import settings
from src.aci.transform import (
    extract_financial_metrics,
    add_derived_metrics,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "sec"
OUTPUT_DIR = ROOT / "data" / "validation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_validation() -> None:
    frames = []

    print("\nAI CAPITAL INTELLIGENCE")
    print("SEC DATA VALIDATION")
    print("=" * 55)

    # Reprocess existing raw files. No SEC requests are made.
    for ticker, company in settings.COMPANIES.items():
        raw_path = RAW_DIR / f"{ticker}_companyfacts.json"

        if not raw_path.exists():
            raise FileNotFoundError(
                f"Missing raw SEC file: {raw_path}"
            )

        print(f"Reading {ticker}: {raw_path.name}")

        with raw_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        frame = extract_financial_metrics(
            payload,
            ticker,
            company["name"],
        )

        print(f"  Extracted observations: {len(frame):,}")

        if not frame.empty:
            frames.append(frame)

    if not frames:
        raise RuntimeError("No financial observations extracted.")

    observations = pd.concat(frames, ignore_index=True)

    # Build a separate canonical period-level dataset.
    canonical = add_derived_metrics(observations)

    # Data-quality checks.
    required_columns = [
        "ticker",
        "metric",
        "period_type",
        "period_start",
        "period_end",
        "value_usd",
    ]

    missing_required = int(
        observations[required_columns].isna().any(axis=1).sum()
    )

    invalid_currency = int(
        (~observations["currency"].eq("USD")).sum()
    )

    invalid_period_type = int(
        (
            ~observations["period_type"].isin(
                ["quarter", "year_to_date", "annual", "rolling_12_month"]
            )
        ).sum()
    )

    negative_capex = int(
        (
            observations.loc[
                observations["metric"].eq("capital_expenditure"),
                "value_usd",
            ] < 0
        ).sum()
    )

    source_duplicate_keys = [
        "ticker",
        "metric",
        "xbrl_tag",
        "period_start",
        "period_end",
        "form",
        "accession_number",
        "reported_value_usd",
    ]

    source_exact_duplicates = int(
        observations.duplicated(
            subset=source_duplicate_keys
        ).sum()
    )

    canonical_keys = [
        "ticker",
        "period_type",
        "period_start",
        "period_end",
    ]

    canonical_duplicate_groups = int(
        canonical.duplicated(
            subset=canonical_keys,
            keep=False,
        ).sum()
    )

    fcf_available = (
        int(canonical["free_cash_flow"].notna().sum())
        if "free_cash_flow" in canonical.columns
        else 0
    )

    fcf_missing = (
        int(canonical["free_cash_flow"].isna().sum())
        if "free_cash_flow" in canonical.columns
        else len(canonical)
    )

    # Period and metric summaries.
    company_counts = (
        observations.groupby("ticker")
        .size()
        .to_dict()
    )

    metric_counts = (
        observations.groupby("metric")
        .size()
        .to_dict()
    )

    period_counts = (
        observations.groupby("period_type")
        .size()
        .to_dict()
    )

    # Preserve all candidate outputs separately from the original files.
    observations_csv = (
        OUTPUT_DIR / "financial_observations_candidate.csv"
    )
    observations_parquet = (
        OUTPUT_DIR / "financial_observations_candidate.parquet"
    )
    canonical_csv = (
        OUTPUT_DIR / "financial_metrics_canonical_candidate.csv"
    )
    canonical_parquet = (
        OUTPUT_DIR / "financial_metrics_canonical_candidate.parquet"
    )

    observations.to_csv(observations_csv, index=False)
    observations.to_parquet(observations_parquet, index=False)

    canonical.to_csv(canonical_csv, index=False)
    canonical.to_parquet(canonical_parquet, index=False)

    checks = {
        "all_four_companies_present": (
            observations["ticker"].nunique() == 4
        ),
        "no_missing_required_fields": missing_required == 0,
        "all_currency_usd": invalid_currency == 0,
        "only_supported_period_types": invalid_period_type == 0,
        "capital_expenditure_non_negative": negative_capex == 0,
        "no_exact_source_duplicates": source_exact_duplicates == 0,
        "no_duplicate_canonical_periods": (
            canonical_duplicate_groups == 0
        ),
    }

    report = {
        "project": "AI Capital Intelligence",
        "validation_type": "local SEC Company Facts reprocessing",
        "network_requests_made": False,
        "source_observations": len(observations),
        "canonical_periods": len(canonical),
        "companies": observations["ticker"].nunique(),
        "company_observation_counts": company_counts,
        "metric_observation_counts": metric_counts,
        "period_type_counts": period_counts,
        "source_exact_duplicate_count": source_exact_duplicates,
        "canonical_duplicate_row_count": canonical_duplicate_groups,
        "missing_required_field_rows": missing_required,
        "non_usd_rows": invalid_currency,
        "unsupported_period_rows": invalid_period_type,
        "negative_capex_rows": negative_capex,
        "fcf_available_periods": fcf_available,
        "fcf_missing_periods": fcf_missing,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "outputs": {
            "observations_csv": str(observations_csv),
            "observations_parquet": str(observations_parquet),
            "canonical_csv": str(canonical_csv),
            "canonical_parquet": str(canonical_parquet),
        },
    }

    report_path = OUTPUT_DIR / "validation_report.json"

    report_path.write_text(
        json.dumps(report, indent=4, default=str),
        encoding="utf-8",
    )

    print("\n" + "=" * 55)
    print("VALIDATION RESULTS")
    print("=" * 55)

    print(f"Source observations: {len(observations):,}")
    print(f"Canonical periods: {len(canonical):,}")
    print(f"Companies: {observations['ticker'].nunique()}")

    print("\nPeriod classifications:")
    for period, count in period_counts.items():
        print(f"  {period}: {count:,}")

    print("\nData-quality checks:")
    for name, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'}: {name}")

    print("\nFCF:")
    print(f"  Available periods: {fcf_available:,}")
    print(f"  Missing periods: {fcf_missing:,}")

    print(f"\nReport: {report_path}")
    print(f"Candidate data: {OUTPUT_DIR}")

    print(
        "\nOverall result:",
        "ALL CHECKS PASSED" if all(checks.values())
        else "REVIEW REQUIRED",
    )


if __name__ == "__main__":
    run_validation()
