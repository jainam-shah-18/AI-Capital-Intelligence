
from __future__ import annotations

import pandas as pd
import pytest

from src.aci.transform import add_derived_metrics


def make_row(
    ticker,
    metric,
    period_type,
    start,
    end,
    value,
    filed,
    accession,
    tag,
):
    return {
        "ticker": ticker,
        "company_name": ticker,
        "metric": metric,
        "xbrl_tag": tag,
        "tag_priority": 0,
        "period_type": period_type,
        "period_start": start,
        "period_end": end,
        "period_days": (
            pd.Timestamp(end) - pd.Timestamp(start)
        ).days + 1,
        "form": "10-Q" if period_type != "annual" else "10-K",
        "filed_date": filed,
        "accession_number": accession,
        "currency": "USD",
        "reported_value_usd": value,
        "value_usd": value,
        "source": "Synthetic regression fixture",
        "data_status": "REPORTED",
    }


@pytest.mark.parametrize(
    "ticker, quarter_start, quarter_end, prior_start, prior_end, "
    "prior_ocf, current_ocf, prior_capex, current_capex, "
    "prior_filed, current_filed, accession, expected_fcf",
    [
        (
            "AMZN",
            "2015-10-01", "2015-12-31",
            "2015-01-01", "2015-09-30",
            3.108, 11.920, 3.280, 4.589,
            "2015-10-23", "2016-01-29",
            "amzn-2015-fy",
            7.503,
        ),
        (
            "AMZN",
            "2016-10-01", "2016-12-31",
            "2016-01-01", "2016-09-30",
            5.791, 16.443, 4.731, 6.737,
            "2016-10-28", "2017-02-10",
            "amzn-2016-fy",
            8.646,
        ),
        (
            "MSFT",
            "2016-04-01", "2016-06-30",
            "2015-07-01", "2016-03-31",
            24.861, 33.325, 5.688, 8.343,
            "2016-04-21", "2016-07-28",
            "msft-fy2016",
            5.809,
        ),
        (
            "MSFT",
            "2017-04-01", "2017-06-30",
            "2016-07-01", "2017-03-31",
            28.502, 39.507, 5.846, 8.129,
            "2017-04-27", "2017-08-02",
            "msft-fy2017",
            8.722,
        ),
    ],
)
def test_common_anchor_annual_reconstruction(
    ticker,
    quarter_start,
    quarter_end,
    prior_start,
    prior_end,
    prior_ocf,
    current_ocf,
    prior_capex,
    current_capex,
    prior_filed,
    current_filed,
    accession,
    expected_fcf,
):
    ocf_tag = (
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"
        if ticker == "MSFT"
        else "NetCashProvidedByUsedInOperatingActivities"
    )

    rows = [
        make_row(
            ticker, "operating_cash_flow", "year_to_date",
            prior_start, prior_end, prior_ocf,
            prior_filed, f"{ticker}-prior-ocf", ocf_tag,
        ),
        make_row(
            ticker, "operating_cash_flow", "annual",
            prior_start, quarter_end, current_ocf,
            current_filed, accession, ocf_tag,
        ),
        make_row(
            ticker, "capital_expenditure", "year_to_date",
            prior_start, prior_end, prior_capex,
            prior_filed, f"{ticker}-prior-capex",
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
        make_row(
            ticker, "capital_expenditure", "annual",
            prior_start, quarter_end, current_capex,
            current_filed, accession,
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
    ]

    result = add_derived_metrics(pd.DataFrame(rows))

    match = result[
        result["ticker"].eq(ticker)
        & result["period_type"].eq("quarter")
        & result["period_start"].eq(quarter_start)
        & result["period_end"].eq(quarter_end)
    ]

    assert len(match) == 1

    row = match.iloc[0]

    assert row["free_cash_flow"] == pytest.approx(expected_fcf)

    assert (
        row["operating_cash_flow_anchor_accession_number"]
        == row["capital_expenditure_anchor_accession_number"]
    )

    assert not bool(row["fcf_vintage_mismatch"])


def test_google_q2_2020_uses_same_h1_filing():
    rows = [
        make_row(
            "GOOGL", "operating_cash_flow", "quarter",
            "2020-01-01", "2020-03-31",
            11.451, "2020-04-29", "googl-q1",
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        make_row(
            "GOOGL", "operating_cash_flow", "year_to_date",
            "2020-01-01", "2020-06-30",
            25.444, "2020-07-31", "googl-h1",
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        make_row(
            "GOOGL", "capital_expenditure", "quarter",
            "2020-04-01", "2020-06-30",
            5.391, "2020-07-31", "googl-h1",
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
    ]

    result = add_derived_metrics(pd.DataFrame(rows))

    row = result[
        result["ticker"].eq("GOOGL")
        & result["period_start"].eq("2020-04-01")
        & result["period_end"].eq("2020-06-30")
    ].iloc[0]

    assert row["operating_cash_flow"] == pytest.approx(13.993)
    assert row["capital_expenditure"] == pytest.approx(5.391)
    assert row["free_cash_flow"] == pytest.approx(8.602)
    assert not bool(row["fcf_vintage_mismatch"])


def test_google_q3_2020_uses_same_nine_month_filing():
    rows = [
        make_row(
            "GOOGL", "operating_cash_flow", "year_to_date",
            "2020-01-01", "2020-06-30",
            25.444, "2020-07-31", "googl-h1",
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        make_row(
            "GOOGL", "operating_cash_flow", "year_to_date",
            "2020-01-01", "2020-09-30",
            42.447, "2020-10-30", "googl-9m",
            "NetCashProvidedByUsedInOperatingActivities",
        ),
        make_row(
            "GOOGL", "capital_expenditure", "quarter",
            "2020-07-01", "2020-09-30",
            5.406, "2020-10-30", "googl-9m",
            "PaymentsToAcquirePropertyPlantAndEquipment",
        ),
    ]

    result = add_derived_metrics(pd.DataFrame(rows))

    row = result[
        result["ticker"].eq("GOOGL")
        & result["period_start"].eq("2020-07-01")
        & result["period_end"].eq("2020-09-30")
    ].iloc[0]

    assert row["operating_cash_flow"] == pytest.approx(17.003)
    assert row["capital_expenditure"] == pytest.approx(5.406)
    assert row["free_cash_flow"] == pytest.approx(11.597)
    assert not bool(row["fcf_vintage_mismatch"])
