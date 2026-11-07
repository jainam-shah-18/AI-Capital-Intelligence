import pandas as pd
import pytest

from src.aci.transform import resolve_duplicate_period_ends


METRICS = [
    "revenue",
    "operating_income",
    "net_income",
    "operating_cash_flow",
    "capital_expenditure",
    "free_cash_flow",
]


def make_duplicate_data():
    """Create two rows for the same canonical period."""
    return pd.DataFrame([
        {
            "ticker": "MSFT",
            "period_type": "quarter",
            "period_end": "2016-09-30",
            "period_start": "2016-07-01",
            "revenue": 21928.0,
            "operating_income": 6715.0,
            "net_income": 5667.0,
            "operating_cash_flow": 11549.0,
            "capital_expenditure": 2163.0,
            "free_cash_flow": 9386.0,
        },
        {
            "ticker": "MSFT",
            "period_type": "quarter",
            "period_end": "2016-09-30",
            "period_start": "2016-07-02",
            "revenue": 21928.0,
            "operating_income": 6715.0,
            "net_income": 5667.0,
            "operating_cash_flow": None,
            "capital_expenditure": None,
            "free_cash_flow": None,
        },
    ])


def test_selects_uniquely_most_complete_row_and_creates_audit():
    df = make_duplicate_data()

    resolved, audit = resolve_duplicate_period_ends(df)

    assert len(resolved) == 1
    assert len(audit) == 2
    assert resolved.iloc[0]["period_start"] == "2016-07-01"
    assert resolved.iloc[0]["operating_cash_flow"] == 11549.0
    assert resolved.duplicated(
        ["ticker", "period_type", "period_end"]
    ).sum() == 0

    selected = audit[audit["selected"]]
    assert len(selected) == 1
    assert selected.iloc[0]["completeness_score"] == 6


def test_rejects_conflicting_financial_values():
    df = make_duplicate_data()
    df.loc[1, "revenue"] = 99999.0

    with pytest.raises(ValueError, match="Conflicting revenue values"):
        resolve_duplicate_period_ends(df)


def test_rejects_tied_completeness_scores():
    df = make_duplicate_data()

    # Make both rows equally complete while keeping shared values identical.
    df.loc[1, "operating_cash_flow"] = 11549.0
    df.loc[1, "capital_expenditure"] = 2163.0
    df.loc[1, "free_cash_flow"] = 9386.0

    with pytest.raises(ValueError, match="Ambiguous duplicate canonical period"):
        resolve_duplicate_period_ends(df)


def test_returns_unchanged_data_and_empty_audit_without_duplicates():
    df = make_duplicate_data().iloc[[0]].copy()

    resolved, audit = resolve_duplicate_period_ends(df)

    assert len(resolved) == 1
    assert resolved.iloc[0]["ticker"] == "MSFT"
    assert audit.empty


def test_handles_empty_dataframe():
    df = pd.DataFrame()

    resolved, audit = resolve_duplicate_period_ends(df)

    assert resolved.empty
    assert audit.empty
