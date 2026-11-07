import pandas as pd

p = "data/validation/financial_metrics_canonical_candidate.csv"
df = pd.read_csv(p)

metrics = [
    "revenue",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "capital_expenditure",
    "free_cash_flow",
]

print("\n" + "=" * 80)
print("AI CAPITAL INTELLIGENCE — PERIOD AND LINEAGE INVESTIGATION")
print("=" * 80)

# A. Show every missing-FCF row with all financial metrics
print("\nA. MISSING FCF — ALL FINANCIAL METRICS")
missing = df[df["free_cash_flow"].isna()]

cols = [
    "ticker", "period_type", "period_start", "period_end",
    *metrics,
    "operating_cash_flow_data_status",
    "capital_expenditure_data_status",
    "operating_cash_flow_xbrl_tag",
    "capital_expenditure_xbrl_tag",
    "operating_cash_flow_source_accession_numbers",
    "capital_expenditure_source_accession_numbers",
]

print(missing[cols].to_string(index=False))

# B. Same company, same period type and end date, multiple start dates
print("\nB. SAME COMPANY / PERIOD TYPE / END DATE WITH MULTIPLE START DATES")

counts = (
    df.groupby(["ticker", "period_type", "period_end"])["period_start"]
      .nunique()
      .reset_index(name="start_date_count")
)

duplicate_ends = counts[counts["start_date_count"] > 1]

if duplicate_ends.empty:
    print("No multiple-start-date groups found.")
else:
    for _, g in duplicate_ends.iterrows():
        subset = df[
            (df["ticker"] == g["ticker"])
            & (df["period_type"] == g["period_type"])
            & (df["period_end"] == g["period_end"])
        ].copy()

        print(
            f"\n{g['ticker']} | {g['period_type']} | "
            f"ending {g['period_end']}"
        )

        detail = [
            "period_start", *metrics,
            "revenue_filed_date",
            "operating_cash_flow_filed_date",
            "capital_expenditure_filed_date",
            "revenue_accession_number",
            "operating_cash_flow_accession_number",
            "capital_expenditure_accession_number",
            "operating_cash_flow_derivation_method",
            "capital_expenditure_derivation_method",
        ]
        print(subset[detail].to_string(index=False))

# C. Rows where every financial metric is missing
print("\nC. ROWS WITH ALL FINANCIAL METRICS MISSING")
all_missing = df[df[metrics].isna().all(axis=1)]

if all_missing.empty:
    print("None.")
else:
    print(
        all_missing[
            ["ticker", "period_type", "period_start", "period_end"]
        ].to_string(index=False)
    )

# D. Reported Alphabet capex lineage
print("\nD. ALPHABET 2020 REPORTED CAPEX LINEAGE")
google = df[
    (df["ticker"] == "GOOGL")
    & (df["period_type"] == "quarter")
    & (df["period_end"].isin(["2020-06-30", "2020-09-30"]))
]

lineage = [
    "period_start", "period_end",
    "capital_expenditure", "capital_expenditure_data_status",
    "capital_expenditure_xbrl_tag",
    "capital_expenditure_filed_date",
    "capital_expenditure_accession_number",
    "capital_expenditure_source_periods",
    "capital_expenditure_source_filed_dates",
    "capital_expenditure_source_accession_numbers",
    "capital_expenditure_anchor_accession_number",
]

print(google[lineage].to_string(index=False))

# E. Summary of period counts
print("\nE. PERIOD COUNTS BY COMPANY AND PERIOD TYPE")
print(
    df.groupby(["ticker", "period_type"])
      .size()
      .unstack(fill_value=0)
      .to_string()
)

print("\nINVESTIGATION COMPLETE")
