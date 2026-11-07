import pandas as pd

from src.aci.transform import extract_financial_metrics, add_derived_metrics


def make_observation(start, end, value, form="10-Q", fy=2025, fp="Q1", filed="2025-05-01", accn="a1"):
    return {"start": start, "end": end, "val": value, "form": form, "fy": fy, "fp": fp, "filed": filed, "accn": accn}


def fixture():
    return {"facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [make_observation("2025-01-01", "2025-03-31", 1000)]}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [make_observation("2025-01-01", "2025-03-31", 400)]}},
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [make_observation("2025-01-01", "2025-03-31", -100)]}},
    }}}


def test_extracts_quarterly_usd_facts():
    df = extract_financial_metrics(fixture(), "TEST", "Test Inc.")
    assert len(df) == 3
    assert set(df["period_type"]) == {"quarter"}
    assert df["currency"].eq("USD").all()


def test_capex_positive_and_fcf_derived():
    df = extract_financial_metrics(fixture(), "TEST", "Test Inc.")
    capex = df.loc[df["metric"] == "capital_expenditure", "value_usd"].iloc[0]
    assert capex == 100
    wide = add_derived_metrics(df)
    assert wide["free_cash_flow"].iloc[0] == 300


def test_filing_metadata_is_not_observation_fiscal_year():
    df = extract_financial_metrics(fixture(), "TEST", "Test Inc.")
    assert "filing_fiscal_year" in df.columns
    assert "filing_fiscal_period" in df.columns
    assert "fiscal_year" not in df.columns
    assert df["filing_fiscal_year"].eq(2025).all()


def test_year_to_date_is_classified_separately():
    data = {"facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [make_observation("2025-01-01", "2025-06-30", 2500, fp="Q2", filed="2025-08-01", accn="a2")]}}}}}
    df = extract_financial_metrics(data, "TEST", "Test Inc.")
    assert len(df) == 1
    assert df["period_type"].iloc[0] == "year_to_date"


def test_annual_observation_requires_annual_filing():
    obs = make_observation("2024-01-01", "2024-12-31", 5000, form="10-K", fp="FY", filed="2025-02-01", accn="annual1")
    data = {"facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [obs]}}}}}
    df = extract_financial_metrics(data, "TEST", "Test Inc.")
    assert len(df) == 1
    assert df["period_type"].iloc[0] == "annual"


def test_same_period_from_different_filings_is_preserved():
    first = make_observation("2025-01-01", "2025-03-31", 1000, filed="2025-05-01", accn="original")
    later = make_observation("2025-01-01", "2025-03-31", 1000, form="10-K", fp="FY", filed="2026-02-01", accn="comparative")
    data = {"facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [first, later]}}}}}
    df = extract_financial_metrics(data, "TEST", "Test Inc.")
    assert len(df) == 2
    assert set(df["accession_number"]) == {"original", "comparative"}


def test_derived_dataset_uses_latest_filing_for_same_period():
    rows = []
    for metric, value in [("revenue", 1000), ("operating_cash_flow", 400), ("capital_expenditure", -100)]:
        for filed, accn in [("2025-05-01", "original"), ("2026-02-01", "comparative")]:
            rows.append({"ticker": "TEST", "metric": metric, "period_type": "quarter", "period_start": "2025-01-01", "period_end": "2025-03-31", "filed_date": filed, "accession_number": accn, "value_usd": value})
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert len(wide) == 1
    assert wide["revenue"].iloc[0] == 1000
    assert wide["free_cash_flow"].iloc[0] == 300


def test_free_cash_flow_not_calculated_when_component_missing():
    data = {"facts": {"us-gaap": {"NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [make_observation("2025-01-01", "2025-03-31", 400)]}}}}}
    df = extract_financial_metrics(data, "TEST", "Test Inc.")
    wide = add_derived_metrics(df)
    assert pd.isna(wide["free_cash_flow"].iloc[0])
    assert wide["free_cash_flow_definition"].iloc[0] == "not_calculated_missing_component"


def test_extracts_both_amazon_capex_candidate_tags():
    data = {"facts": {"us-gaap": {
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [make_observation("2016-01-01", "2016-12-31", 6737000000, form="10-K", fp="FY", accn="oldtag")] }},
        "PaymentsToAcquireProductiveAssets": {"units": {"USD": [make_observation("2016-01-01", "2016-12-31", 7804000000, form="10-K", fp="FY", filed="2019-02-01", accn="newtag"), make_observation("2017-01-01", "2017-12-31", 11955000000, form="10-K", fp="FY", filed="2019-02-01", accn="newtag2")] }},
    }}}
    df = extract_financial_metrics(data, "AMZN", "Amazon")
    capex = df[df.metric.eq("capital_expenditure")]
    assert set(capex.xbrl_tag) == {"PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"}
    assert len(capex) == 3


def test_canonical_capex_prefers_ppande_tag_for_same_period():
    data = {"facts": {"us-gaap": {
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": [make_observation("2016-01-01", "2016-12-31", 6737000000, form="10-K", fp="FY", accn="oldtag")] }},
        "PaymentsToAcquireProductiveAssets": {"units": {"USD": [make_observation("2016-01-01", "2016-12-31", 7804000000, form="10-K", fp="FY", filed="2019-02-01", accn="newtag")] }},
    }}}
    df = extract_financial_metrics(data, "AMZN", "Amazon")
    wide = add_derived_metrics(df)
    assert wide["capital_expenditure"].iloc[0] == 6737000000
    assert wide["capital_expenditure_xbrl_tag"].iloc[0] == "PaymentsToAcquirePropertyPlantAndEquipment"
    assert bool(wide["capital_expenditure_tag_conflict"].iloc[0]) is True


def test_12_month_duration_in_10q_is_rolling_not_annual():
    obs = make_observation("2019-10-01", "2020-09-30", 30629000000, form="10-Q", fp="Q3")
    data = {"facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [obs]}}}}}
    df = extract_financial_metrics(data, "TEST", "Test Inc.")
    assert df["period_type"].iloc[0] == "rolling_12_month"


def _observation(metric, value, start, end, period_type, filed, accn, tag="TestTag", priority=0):
    return {"ticker": "TEST", "metric": metric, "period_type": period_type,
            "period_start": start, "period_end": end,
            "period_days": (pd.Timestamp(end) - pd.Timestamp(start)).days + 1,
            "filed_date": filed, "accession_number": accn, "value_usd": value,
            "xbrl_tag": tag, "tag_priority": priority, "data_status": "REPORTED"}


def test_reconstructs_q2_from_h1_ytd_minus_q1():
    rows = [
        _observation("revenue", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "q1"),
        _observation("revenue", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q2 = wide[(wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")]
    assert len(q2) == 1
    assert q2.revenue.iloc[0] == 160
    assert q2.revenue_data_status.iloc[0] == "DERIVED"


def test_reconstructs_q3_from_9m_minus_h1():
    rows = [
        _observation("revenue", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1"),
        _observation("revenue", 420, "2025-01-01", "2025-09-30", "year_to_date", "2025-11-01", "m9"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q3 = wide[(wide.period_start == "2025-07-01") & (wide.period_end == "2025-09-30")]
    assert len(q3) == 1
    assert q3.revenue.iloc[0] == 160
    assert q3.revenue_data_status.iloc[0] == "DERIVED"


def test_reconstructs_q4_from_annual_minus_9m():
    rows = [
        _observation("revenue", 420, "2025-01-01", "2025-09-30", "year_to_date", "2025-11-01", "m9"),
        _observation("revenue", 600, "2025-01-01", "2025-12-31", "annual", "2026-02-01", "fy"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q4 = wide[(wide.period_start == "2025-10-01") & (wide.period_end == "2025-12-31")]
    assert len(q4) == 1
    assert q4.revenue.iloc[0] == 180
    assert q4.revenue_data_status.iloc[0] == "DERIVED"


def test_reported_quarter_takes_precedence_over_reconstruction():
    rows = [
        _observation("revenue", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "q1"),
        _observation("revenue", 155, "2025-04-01", "2025-06-30", "quarter", "2025-08-01", "q2direct"),
        _observation("revenue", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q2 = wide[(wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")]
    assert q2.revenue.iloc[0] == 155
    assert q2.revenue_data_status.iloc[0] == "REPORTED"


def test_does_not_reconstruct_without_previous_cumulative_value():
    rows = [_observation("revenue", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1")]
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert not ((wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")).any()


def test_reconstruction_uses_actual_53_week_fiscal_dates():
    rows = [
        _observation("revenue", 100, "2024-02-04", "2024-05-04", "quarter", "2024-06-01", "q1"),
        _observation("revenue", 265, "2024-02-04", "2024-08-03", "year_to_date", "2024-09-01", "h1"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q2 = wide[(wide.period_start == "2024-05-05") & (wide.period_end == "2024-08-03")]
    assert len(q2) == 1
    assert q2.revenue.iloc[0] == 165


def test_does_not_reconstruct_across_different_xbrl_tags():
    rows = [
        _observation("capital_expenditure", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "q1", tag="TagA"),
        _observation("capital_expenditure", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1", tag="TagB"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert not ((wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")).any()


def test_fcf_not_calculated_when_filing_vintages_mismatch():
    rows = [
        _observation("operating_cash_flow", 400, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "ocf-v1"),
        _observation("capital_expenditure", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "capex-v2"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert pd.isna(wide.free_cash_flow.iloc[0])
    assert bool(wide.fcf_vintage_mismatch.iloc[0]) is True
    assert wide.free_cash_flow_definition.iloc[0] == "not_calculated_anchor_filing_mismatch"


def test_reconstructed_metrics_retain_source_lineage():
    rows = [
        _observation("revenue", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "q1"),
        _observation("revenue", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q2 = wide[(wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")]
    assert "q1" in q2.revenue_source_accession_numbers.iloc[0]
    assert "h1" in q2.revenue_source_accession_numbers.iloc[0]
    assert q2.revenue_derivation_method.iloc[0] == "current_cumulative_minus_previous_cumulative_same_tag_asof"


def test_reconstructed_ocf_uses_anchor_filing_not_full_lineage_for_fcf():
    rows = [
        _observation("operating_cash_flow", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "q1"),
        _observation("operating_cash_flow", 260, "2025-01-01", "2025-06-30", "year_to_date", "2025-08-01", "h1"),
        _observation("capital_expenditure", 80, "2025-04-01", "2025-06-30", "quarter", "2025-08-01", "h1"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q2 = wide[(wide.period_start == "2025-04-01") & (wide.period_end == "2025-06-30")]
    assert len(q2) == 1
    assert q2.operating_cash_flow.iloc[0] == 160
    assert q2.operating_cash_flow_anchor_accession_number.iloc[0] == "h1"
    assert q2.capital_expenditure_anchor_accession_number.iloc[0] == "h1"
    assert q2.free_cash_flow.iloc[0] == 80
    assert bool(q2.fcf_vintage_mismatch.iloc[0]) is False
    # The prior Q1 accession remains in the audit lineage.
    assert "q1" in q2.operating_cash_flow_source_accession_numbers.iloc[0]
    assert "h1" in q2.operating_cash_flow_source_accession_numbers.iloc[0]


def test_q4_reconstructed_metrics_share_annual_anchor_for_fcf():
    rows = [
        _observation("operating_cash_flow", 420, "2025-01-01", "2025-09-30", "year_to_date", "2025-11-01", "m9"),
        _observation("operating_cash_flow", 600, "2025-01-01", "2025-12-31", "annual", "2026-02-01", "fy"),
        _observation("capital_expenditure", 90, "2025-01-01", "2025-09-30", "year_to_date", "2025-11-01", "m9"),
        _observation("capital_expenditure", 130, "2025-01-01", "2025-12-31", "annual", "2026-02-01", "fy"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    q4 = wide[(wide.period_start == "2025-10-01") & (wide.period_end == "2025-12-31")]
    assert len(q4) == 1
    assert q4.operating_cash_flow.iloc[0] == 180
    assert q4.capital_expenditure.iloc[0] == 40
    assert q4.operating_cash_flow_anchor_accession_number.iloc[0] == "fy"
    assert q4.capital_expenditure_anchor_accession_number.iloc[0] == "fy"
    assert q4.free_cash_flow.iloc[0] == 140
    assert bool(q4.fcf_vintage_mismatch.iloc[0]) is False


def test_different_anchor_filing_accessions_still_block_fcf():
    rows = [
        _observation("operating_cash_flow", 400, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "ocf-filing"),
        _observation("capital_expenditure", 100, "2025-01-01", "2025-03-31", "quarter", "2025-05-01", "capex-filing"),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert pd.isna(wide.free_cash_flow.iloc[0])
    assert bool(wide.fcf_vintage_mismatch.iloc[0]) is True
    assert wide.free_cash_flow_definition.iloc[0] == "not_calculated_anchor_filing_mismatch"


def test_amazon_capex_conflict_remains_flagged_after_anchor_logic():
    rows = [
        _observation("operating_cash_flow", 17203, "2016-01-01", "2016-12-31", "annual", "2019-02-01", "ocf-2019"),
        _observation("capital_expenditure", 6737, "2016-01-01", "2016-12-31", "annual", "2017-02-10", "capex-2017", tag="PaymentsToAcquirePropertyPlantAndEquipment", priority=0),
        _observation("capital_expenditure", 7804, "2016-01-01", "2016-12-31", "annual", "2019-02-01", "capex-2019", tag="PaymentsToAcquireProductiveAssets", priority=1),
    ]
    wide = add_derived_metrics(pd.DataFrame(rows))
    assert bool(wide.capital_expenditure_tag_conflict.iloc[0]) is True
    assert pd.isna(wide.free_cash_flow.iloc[0])
    assert bool(wide.fcf_vintage_mismatch.iloc[0]) is True



def test_extracts_microsoft_continuing_operations_ocf_tag():
    data = {
        "facts": {
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", 400,
                                accn="original"
                            )
                        ]
                    }
                },
                "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", 420,
                                accn="continuing"
                            )
                        ]
                    }
                },
            }
        }
    }

    df = extract_financial_metrics(data, "MSFT", "Microsoft")

    ocf = df[df.metric.eq("operating_cash_flow")]

    assert len(ocf) == 2
    assert set(ocf.xbrl_tag) == {
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    }


def test_microsoft_continuing_operations_tag_is_preferred():
    data = {
        "facts": {
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivities": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", 400,
                                accn="original"
                            )
                        ]
                    }
                },
                "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", 420,
                                accn="continuing"
                            )
                        ]
                    }
                },
            }
        }
    }

    df = extract_financial_metrics(data, "MSFT", "Microsoft")
    wide = add_derived_metrics(df)

    assert wide.operating_cash_flow.iloc[0] == 420
    assert (
        wide.operating_cash_flow_xbrl_tag.iloc[0]
        == "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"
    )


def test_microsoft_continuing_operations_ocf_supports_same_filing_fcf():
    data = {
        "facts": {
            "us-gaap": {
                "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", 400,
                                accn="microsoft-filing"
                            )
                        ]
                    }
                },
                "PaymentsToAcquirePropertyPlantAndEquipment": {
                    "units": {
                        "USD": [
                            make_observation(
                                "2025-01-01", "2025-03-31", -100,
                                accn="microsoft-filing"
                            )
                        ]
                    }
                },
            }
        }
    }

    df = extract_financial_metrics(data, "MSFT", "Microsoft")
    wide = add_derived_metrics(df)

    assert wide.operating_cash_flow.iloc[0] == 400
    assert wide.capital_expenditure.iloc[0] == 100
    assert wide.free_cash_flow.iloc[0] == 300
    assert bool(wide.fcf_vintage_mismatch.iloc[0]) is False
