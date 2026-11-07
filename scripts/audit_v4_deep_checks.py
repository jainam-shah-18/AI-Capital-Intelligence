import json
from pathlib import Path
import pandas as pd

BASE = Path("data")

def load_facts(ticker):
    path = BASE / "raw" / "sec" / f"{ticker}_companyfacts.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)["facts"]["us-gaap"]

def print_fact_rows(ticker, tags, target_end, target_starts=None):
    facts = load_facts(ticker)
    print(f"\n{'='*90}")
    print(f"{ticker} — RAW SEC FACTS — END DATE {target_end}")
    print(f"{'='*90}")

    for tag in tags:
        fact = facts.get(tag, {})
        observations = fact.get("units", {}).get("USD", [])

        matches = [
            x for x in observations
            if x.get("end") == target_end
            and x.get("form") in {"10-Q", "10-K", "20-F", "40-F"}
            and (
                target_starts is None
                or x.get("start") in target_starts
            )
        ]

        if matches:
            print(f"\nTAG: {tag}")
            for x in sorted(
                matches,
                key=lambda z: (z.get("filed", ""), z.get("accn", ""))
            ):
                print({
                    "start": x.get("start"),
                    "end": x.get("end"),
                    "value": x.get("val"),
                    "form": x.get("form"),
                    "filed": x.get("filed"),
                    "accession": x.get("accn"),
                    "fy": x.get("fy"),
                    "fp": x.get("fp"),
                })

# 1. Amazon: inspect both candidate capex tags and OCF.
print_fact_rows(
    "AMZN",
    [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "NetCashProvidedByUsedInOperatingActivities",
    ],
    "2017-06-30",
    ["2017-04-01", "2017-01-01"],
)

# 2. Microsoft: investigate both start dates for the same end date.
print_fact_rows(
    "MSFT",
    [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "Revenues",
        "OperatingIncomeLoss",
        "NetIncomeLoss",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "NetCashProvidedByUsedInOperatingActivities",
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "2016-09-30",
    ["2016-07-01", "2016-07-02"],
)

# 3. Audit full source lineage for every FCF observation.
path = BASE / "validation" / "financial_metrics_canonical_candidate.csv"
df = pd.read_csv(path)

fcf = df[df["free_cash_flow"].notna()].copy()

lineage_columns = [
    "ticker",
    "period_type",
    "period_start",
    "period_end",
    "operating_cash_flow_data_status",
    "capital_expenditure_data_status",
    "operating_cash_flow_anchor_accession_number",
    "capital_expenditure_anchor_accession_number",
    "operating_cash_flow_source_accession_numbers",
    "capital_expenditure_source_accession_numbers",
]

print(f"\n{'='*90}")
print("FCF SOURCE LINEAGE AUDIT")
print(f"{'='*90}")

for col in lineage_columns:
    if col not in fcf.columns:
        print("MISSING COLUMN:", col)

available = [c for c in lineage_columns if c in fcf.columns]
print(fcf[available].to_string(index=False))

def source_set(value):
    if pd.isna(value) or not str(value).strip():
        return set()
    return set(str(value).split("|"))

def lineage_check(row):
    ocf_anchor = row.get("operating_cash_flow_anchor_accession_number")
    capex_anchor = row.get("capital_expenditure_anchor_accession_number")

    if pd.isna(ocf_anchor) or pd.isna(capex_anchor):
        return "ANCHOR_MISSING"

    if str(ocf_anchor) != str(capex_anchor):
        return "ANCHOR_MISMATCH"

    ocf_status = row.get("operating_cash_flow_data_status")
    capex_status = row.get("capital_expenditure_data_status")

    ocf_sources = source_set(
        row.get("operating_cash_flow_source_accession_numbers")
    )
    capex_sources = source_set(
        row.get("capital_expenditure_source_accession_numbers")
    )

    if ocf_status == "DERIVED" and capex_status == "DERIVED":
        if ocf_sources == capex_sources:
            return "SAME_FULL_SOURCE_SET"
        return "DIFFERENT_FULL_SOURCE_SETS"

    if ocf_status == "REPORTED" and capex_status == "REPORTED":
        return "BOTH_REPORTED_SAME_ANCHOR"

    return "MIXED_REPORTED_DERIVED"

fcf["lineage_check"] = fcf.apply(lineage_check, axis=1)

print("\nLINEAGE CHECK SUMMARY")
print(fcf["lineage_check"].value_counts(dropna=False).to_string())

print("\nFCF ROWS REQUIRING LINEAGE REVIEW")
review = fcf[
    ~fcf["lineage_check"].isin([
        "SAME_FULL_SOURCE_SET",
        "BOTH_REPORTED_SAME_ANCHOR",
    ])
]

review_columns = [
    c for c in available + ["lineage_check"]
    if c in review.columns
]
print(review[review_columns].to_string(index=False))

print("\nDEEP CHECKS COMPLETE")
