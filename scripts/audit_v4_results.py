import pandas as pd

PATH = "data/validation/financial_metrics_canonical_candidate.csv"
df = pd.read_csv(PATH)

for col in ["fcf_vintage_mismatch", "capital_expenditure_tag_conflict"]:
    df[col] = df[col].astype(str).str.lower().map(
        {"true": True, "false": False}
    ).fillna(False)

money = [
    "capital_expenditure",
    "operating_cash_flow",
    "free_cash_flow",
]

print("\n" + "=" * 75)
print("AI CAPITAL INTELLIGENCE — v4 FINANCIAL RECONCILIATION AUDIT")
print("=" * 75)

# 1. Canonical row counts by company and period type
print("\n1. CANONICAL PERIOD COUNTS")
print(
    df.groupby(["ticker", "period_type"])
      .size()
      .unstack(fill_value=0)
      .to_string()
)
print("\nTotal canonical rows:", len(df))

# 2. FCF availability by company and period type
print("\n2. FCF AVAILABILITY BY COMPANY AND PERIOD TYPE")
df["fcf_available"] = df["free_cash_flow"].notna()
print(
    df.groupby(["ticker", "period_type"])["fcf_available"]
      .agg(["sum", "count"])
      .to_string()
)

# 3. Vintage mismatch flags
print("\n3. FCF VINTAGE MISMATCH FLAGS")
print("Total flagged rows:", int(df["fcf_vintage_mismatch"].sum()))
mismatch = df[df["fcf_vintage_mismatch"]]
if mismatch.empty:
    print("No rows flagged.")
else:
    cols = [
        "ticker", "period_type", "period_start", "period_end",
        "operating_cash_flow", "capital_expenditure",
        "operating_cash_flow_anchor_accession_number",
        "capital_expenditure_anchor_accession_number",
        "fcf_vintage_mismatch",
    ]
    print(mismatch[cols].to_string(index=False))

# 4. Verify accessions for rows with calculated FCF
print("\n4. FCF ANCHOR ACCESSION COMPATIBILITY")
available = df[df["free_cash_flow"].notna()].copy()
available["anchor_accessions_match"] = (
    available["operating_cash_flow_anchor_accession_number"].notna()
    & available["capital_expenditure_anchor_accession_number"].notna()
    & (
        available["operating_cash_flow_anchor_accession_number"]
        == available["capital_expenditure_anchor_accession_number"]
    )
)
print("Rows with FCF:", len(available))
print(
    "Rows with matching non-null anchor accessions:",
    int(available["anchor_accessions_match"].sum())
)
print(
    "Rows with non-matching or missing anchor accessions:",
    int((~available["anchor_accessions_match"]).sum())
)

# 5. Capital expenditure tag conflicts
print("\n5. CAPITAL EXPENDITURE TAG CONFLICTS")
conflicts = df[df["capital_expenditure_tag_conflict"]]
print("Total conflict-flagged canonical rows:", len(conflicts))
if conflicts.empty:
    print("No conflict-flagged rows found.")
else:
    cols = [
        "ticker", "period_type", "period_start", "period_end",
        "capital_expenditure", "capital_expenditure_xbrl_tag",
        "capital_expenditure_filed_date",
        "capital_expenditure_accession_number",
        "capital_expenditure_tag_conflict",
    ]
    print(conflicts[cols].to_string(index=False))

# 6. Six reconstructed-quarter checks
B = 1_000_000_000
targets = [
    ("AMZN", "2015-12-31", 8.812, 1.309, 7.503),
    ("AMZN", "2016-12-31", 10.652, 2.006, 8.646),
    ("GOOGL", "2020-06-30", 13.993, 5.391, 8.602),
    ("GOOGL", "2020-09-30", 17.003, 5.406, 11.597),
    ("MSFT", "2016-06-30", 8.464, 2.655, 5.809),
    ("MSFT", "2017-06-30", 11.005, 2.283, 8.722),
]

print("\n6. SIX RECONSTRUCTED-QUARTER CHECKS")
for ticker, end_date, exp_ocf, exp_capex, exp_fcf in targets:
    row = df[
        (df["ticker"] == ticker)
        & (df["period_type"] == "quarter")
        & (df["period_end"] == end_date)
    ]

    print(f"\n{ticker} quarter ending {end_date}:")
    if row.empty:
        print("  NOT FOUND")
        continue

    for _, r in row.iterrows():
        actuals = {
            "operating_cash_flow": r["operating_cash_flow"],
            "capital_expenditure": r["capital_expenditure"],
            "free_cash_flow": r["free_cash_flow"],
        }
        expected = {
            "operating_cash_flow": exp_ocf * B,
            "capital_expenditure": exp_capex * B,
            "free_cash_flow": exp_fcf * B,
        }

        for metric in actuals:
            value = actuals[metric]
            expected_value = expected[metric]
            if pd.isna(value):
                print(f"  {metric}: MISSING (expected ${expected_value/B:.3f}B)")
            else:
                delta = (value - expected_value) / B
                print(
                    f"  {metric}: ${value/B:.3f}B | "
                    f"expected ${expected_value/B:.3f}B | "
                    f"difference ${delta:+.3f}B"
                )

        print("  OCF tag:", r.get("operating_cash_flow_xbrl_tag"))
        print("  Capex tag:", r.get("capital_expenditure_xbrl_tag"))
        print(
            "  OCF anchor:",
            r.get("operating_cash_flow_anchor_accession_number")
        )
        print(
            "  Capex anchor:",
            r.get("capital_expenditure_anchor_accession_number")
        )
        print(
            "  OCF derivation:",
            r.get("operating_cash_flow_derivation_method")
        )
        print(
            "  Capex derivation:",
            r.get("capital_expenditure_derivation_method")
        )

print("\n" + "=" * 75)
print("AUDIT COMPLETE — review results before approving Snowflake loading")
print("=" * 75)
