import pandas as pd

path = "data/validation/financial_metrics_canonical_candidate.csv"
df = pd.read_csv(path)

keys = ["ticker", "period_type", "period_end"]

duplicates = df[df.duplicated(keys, keep=False)].copy()

print("\nDUPLICATE COMPANY / PERIOD TYPE / END DATE")
if duplicates.empty:
    print("None")
else:
    for key, group in duplicates.groupby(keys):
        print("\n", key)
        cols = [
            "period_start",
            "period_end",
            "revenue",
            "operating_income",
            "net_income",
            "operating_cash_flow",
            "capital_expenditure",
            "free_cash_flow",
        ]
        print(group[cols].to_string(index=False))

print("\nDUPLICATE KEY SUMMARY")
print(
    duplicates.groupby("ticker")
    .size()
    .to_string()
)

print("\nAUDIT COMPLETE")
