from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / "data/validation/financial_metrics_canonical_candidate.csv"
OUTPUT = BASE / "data/validation/financial_metrics_canonical_final_candidate.csv"
AUDIT = BASE / "data/validation/period_end_resolution_audit.csv"

df = pd.read_csv(SOURCE)

keys = ["ticker", "period_type", "period_end"]
metrics = [
    "revenue",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "capital_expenditure",
    "free_cash_flow",
]

df["_period_start_sort"] = pd.to_datetime(
    df["period_start"], errors="coerce"
)
df["_completeness"] = df[metrics].notna().sum(axis=1)

duplicate_mask = df.duplicated(keys, keep=False)
duplicates = df[duplicate_mask].copy()

selected_indices = []
audit_rows = []

for key, group in duplicates.groupby(keys, dropna=False):
    # Do not automatically resolve conflicting reported values.
    for metric in metrics:
        values = group[metric].dropna()
        if len(values) > 1 and not values.max() == values.min():
            raise ValueError(
                f"Conflicting values for {key}, metric={metric}: "
                f"{values.tolist()}. Manual review required."
            )

    ranked = group.sort_values(
        ["_completeness", "_period_start_sort"],
        ascending=[False, True],
        na_position="last",
    )

    winner = ranked.index[0]
    selected_indices.append(winner)

    for idx, row in group.iterrows():
        audit_rows.append({
            "ticker": key[0],
            "period_type": key[1],
            "period_end": key[2],
            "period_start": row["period_start"],
            "completeness_score": int(row["_completeness"]),
            "selected_as_canonical": idx == winner,
            "selection_reason": (
                "Most complete metrics; earliest period start "
                "when completeness ties"
            ),
        })

# Retain all non-duplicate rows and one selected row per duplicate group.
non_duplicates = df[~duplicate_mask]
selected_duplicates = df.loc[selected_indices]

result = pd.concat(
    [non_duplicates, selected_duplicates],
    ignore_index=True,
)

result = result.drop(
    columns=["_period_start_sort", "_completeness"],
    errors="ignore",
)

audit = pd.DataFrame(audit_rows)

result.to_csv(OUTPUT, index=False)
audit.to_csv(AUDIT, index=False)

print("INPUT ROWS:", len(df))
print("DUPLICATE ROWS REVIEWED:", len(duplicates))
print("DUPLICATE GROUPS:", len(audit) // 2)
print("OUTPUT ROWS:", len(result))
print("REMAINING DUPLICATE KEYS:", int(result.duplicated(keys).sum()))
print("CANONICAL CANDIDATE:", OUTPUT)
print("RESOLUTION AUDIT:", AUDIT)
