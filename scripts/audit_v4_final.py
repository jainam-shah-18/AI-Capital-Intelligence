import pandas as pd

p = "data/validation/financial_metrics_canonical_candidate.csv"
df = pd.read_csv(p)

print("\n1. ALL 10 PERIODS WITH MISSING FCF")
missing = df[df["free_cash_flow"].isna()]

cols = [
    "ticker", "period_type", "period_start", "period_end",
    "operating_cash_flow", "capital_expenditure",
    "operating_cash_flow_xbrl_tag",
    "capital_expenditure_xbrl_tag",
    "operating_cash_flow_data_status",
    "capital_expenditure_data_status",
    "operating_cash_flow_anchor_accession_number",
    "capital_expenditure_anchor_accession_number",
]

print(missing[cols].to_string(index=False))

print("\n2. GOOGLE Q2/Q3 2020 CAPEX LINEAGE")
google = df[
    (df["ticker"] == "GOOGL")
    & (df["period_end"].isin(["2020-06-30", "2020-09-30"]))
    & (df["period_type"] == "quarter")
]

lineage_cols = [
    "ticker", "period_start", "period_end",
    "capital_expenditure", "capital_expenditure_data_status",
    "capital_expenditure_derivation_method",
    "capital_expenditure_source_periods",
    "capital_expenditure_source_filed_dates",
    "capital_expenditure_source_accession_numbers",
    "capital_expenditure_anchor_accession_number",
    "operating_cash_flow_anchor_accession_number",
]

print(google[lineage_cols].to_string(index=False))

print("\n3. CANONICAL PERIODS BY COMPANY")
print(
    df.groupby("ticker")
      .agg(
          canonical_periods=("period_end", "size"),
          unique_period_ends=("period_end", "nunique")
      )
      .to_string()
)

print("\n4. ALL CANONICAL PERIODS BY COMPANY")
for ticker, group in df.groupby("ticker"):
    print(f"\n{ticker}")
    print(
        group[["period_type", "period_start", "period_end"]]
        .sort_values(["period_end", "period_type"])
        .to_string(index=False)
    )

print("\nAUDIT COMPLETE")
