
from decimal import Decimal

from src.aci.ai_retrieval import (
    retrieve_company_performance,
    retrieve_cash_flow,
    retrieve_company_comparison,
    retrieve_revenue_forecast,
    retrieve_financial_anomalies,
    retrieve_financial_risk,
)


def format_billions(value):
    if value is None:
        return "Not available"

    return (
        f"${Decimal(str(value)) / Decimal('1000000000'):.2f} billion"
    )


def format_percentage(value):
    if value is None:
        return "Not available"

    return f"{Decimal(str(value)):.2f}%"


def ask_company_performance(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_company_performance(company_name, limit)

    if not rows:
        return {
            "status": "NO_DATA",
            "company": company_name,
            "answer_source": "SNOWFLAKE_DIRECT",
            "answer": "No financial records were found."
        }

    latest = rows[0]

    answer = (
        f"{latest['COMPANY_NAME']} financial performance "
        f"for the period ending {latest['PERIOD_END']}:\n\n"

        f"Revenue: {format_billions(latest['REVENUE'])}.\n"
        f"Operating income: {format_billions(latest['OPERATING_INCOME'])}.\n"
        f"Net income: {format_billions(latest['NET_INCOME'])}.\n"
        f"Operating cash flow: "
        f"{format_billions(latest['OPERATING_CASH_FLOW'])}.\n"
        f"CAPEX: {format_billions(latest['CAPEX'])}.\n\n"

        f"Operating margin: "
        f"{format_percentage(latest['OPERATING_MARGIN_PCT'])}.\n"
        f"Net profit margin: "
        f"{format_percentage(latest['NET_PROFIT_MARGIN_PCT'])}.\n\n"

        f"Revenue QoQ growth: "
        f"{format_percentage(latest['REVENUE_QOQ_GROWTH_PCT'])}.\n"
        f"Revenue YoY growth: "
        f"{format_percentage(latest['REVENUE_YOY_GROWTH_PCT'])}.\n\n"

        "Growth percentages are database-reported revenue metrics only. "
        "Growth rates for operating income, net income, operating cash "
        "flow and CAPEX are not calculated or inferred here.\n\n"

        "Free cash flow is excluded from this performance summary "
        "because its CAPEX reporting basis requires review. "
        "No unsupported free cash flow figure is presented.\n\n"

        "This summary uses the latest retrieved financial record. "
        "It does not infer longer-term trends from the available records."
    )

    return {
        "status": "SUCCESS",
        "company": latest["COMPANY_NAME"],
        "records_used": len(rows),
        "latest_period": str(latest["PERIOD_END"]),
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }


def ask_cash_flow(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_cash_flow(company_name, limit)

    if not rows:
        return {
            "status": "NO_DATA",
            "company": company_name,
            "answer": "No cash-flow records were found."
        }

    latest = rows[0]

    operating_cash_flow = latest["OPERATING_CASH_FLOW"]
    capex = latest["CAPEX_REPORTED_VALUE"]
    free_cash_flow = latest["FREE_CASH_FLOW"]

    fcf_status = latest["FREE_CASH_FLOW_STATUS"]
    capex_quality = latest["CAPEX_QUALITY_STATUS"]
    reporting_basis = latest["CAPEX_REPORTING_BASIS"]

    answer = (
        f"{latest['COMPANY_NAME']} cash-flow information for the "
        f"period ending {latest['PERIOD_END']}:\n"
        f"Operating cash flow: {format_billions(operating_cash_flow)}.\n"
        f"Reported CAPEX: {format_billions(capex)}.\n"
    )

    if free_cash_flow is not None:
        answer += (
            f"Free cash flow: {format_billions(free_cash_flow)}.\n"
        )
    else:
        answer += (
            "Verified free cash flow is not available because the "
            f"CAPEX basis requires review ({fcf_status}).\n"
        )

    answer += (
        f"CAPEX quality status: {capex_quality}.\n"
        f"CAPEX reporting basis: {reporting_basis}."
    )

    return {
        "status": "SUCCESS",
        "company": latest["COMPANY_NAME"],
        "latest_period": str(latest["PERIOD_END"]),
        "records_used": len(rows),
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }


def ask_company_comparison(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_company_comparison(company_name, limit)

    if not rows:
        return {
            "status": "NO_DATA",
            "company": company_name,
            "answer": "No company comparison records were found."
        }

    latest = rows[0]

    revenue = format_billions(latest["REVENUE"])
    peer_average = format_billions(latest["PEER_AVG_REVENUE"])

    rank = latest["REVENUE_RANK"]
    company_count = latest["COMPARISON_COMPANY_COUNT"]

    margin = latest["OPERATING_MARGIN_PCT"]
    peer_margin = latest["PEER_AVG_OPERATING_MARGIN_PCT"]

    rank_text = (
        f"{rank} out of {company_count} companies"
        if rank is not None and company_count is not None
        else "Not available"
    )

    margin_text = format_percentage(margin)
    peer_margin_text = format_percentage(peer_margin)

    answer = (
        f"{latest['COMPANY_NAME']} company comparison "
        f"for the period ending {latest['PERIOD_END']}:\n"
        f"Revenue: {revenue}.\n"
        f"Peer average revenue: {peer_average}.\n"
        f"Revenue rank: {rank_text}.\n"
        f"Operating margin: {margin_text}.\n"
        f"Peer average operating margin: {peer_margin_text}.\n"
        "All comparison metrics are retrieved directly "
        "from Snowflake without recalculation."
    )

    return {
        "status": "SUCCESS",
        "company": latest["COMPANY_NAME"],
        "latest_period": str(latest["PERIOD_END"]),
        "records_used": len(rows),
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }


def ask_revenue_forecast(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_revenue_forecast(company_name, limit)

    forecast_rows = [
        row for row in rows
        if row["FORECAST_RECORD_TYPE"] == "NEXT_QUARTER_FORECAST"
    ]

    if not forecast_rows:
        return {
            "status": "NO_FORECAST",
            "company": company_name,
            "answer_source": "SNOWFLAKE_DIRECT",
            "answer": "No next-quarter revenue forecast is available."
        }

    forecast = forecast_rows[0]

    forecast_value = format_billions(forecast["FORECAST_REVENUE"])
    target_period = forecast["TARGET_PERIOD_END"]
    source_period = forecast["FORECAST_SOURCE_PERIOD_END"]

    answer = (
        f"The database revenue forecast for {forecast['COMPANY_NAME']} "
        f"for the period ending {target_period} is {forecast_value}. "
        f"The forecast source period is {source_period}. "
        "This is a model-generated forecast, not reported actual revenue "
        "or company guidance."
    )

    return {
        "status": "SUCCESS",
        "company": forecast["COMPANY_NAME"],
        "target_period": str(target_period),
        "forecast_source_period": str(source_period),
        "forecast_revenue": forecast["FORECAST_REVENUE"],
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }


def ask_financial_anomalies(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_financial_anomalies(company_name, limit)

    if not rows:
        return {
            "status": "NO_DATA",
            "company": company_name,
            "answer_source": "SNOWFLAKE_DIRECT",
            "answer": "No financial anomaly records were found."
        }

    flagged = [
        row for row in rows
        if str(row["ANOMALY_STATUS"]).upper() == "ANOMALY"
    ]

    latest_period = max(row["PERIOD_END"] for row in rows)

    if flagged:
        details = []

        for row in flagged:
            z_score = row["ANOMALY_Z_SCORE"]

            z_text = (
                "Not available"
                if z_score is None
                else f"{float(z_score):.2f}"
            )

            details.append(
                f"{row['METRIC_NAME']} for period "
                f"{row['PERIOD_END']} has an anomaly status "
                f"with a Z-score of {z_text}."
            )

        answer = (
            f"{rows[0]['COMPANY_NAME']} has {len(flagged)} flagged "
            f"anomaly record(s) among the {len(rows)} retrieved records. "
            + " ".join(details)
        )

    else:
        answer = (
            f"No anomalies were flagged among the {len(rows)} retrieved "
            f"records for {rows[0]['COMPANY_NAME']}."
        )

    return {
        "status": "SUCCESS",
        "company": rows[0]["COMPANY_NAME"],
        "latest_period": str(latest_period),
        "records_used": len(rows),
        "anomalies_found": len(flagged),
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }


def ask_financial_risk(
    company_name: str,
    question: str,
    limit: int = 8
) -> dict:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    rows = retrieve_financial_risk(company_name, limit)

    if not rows:
        return {
            "status": "NO_DATA",
            "company": company_name,
            "answer_source": "SNOWFLAKE_DIRECT",
            "answer": "No financial risk monitoring records were found."
        }

    latest = max(rows, key=lambda row: row["PERIOD_END"])

    flag_names = [
        "REVENUE_GROWTH_DECLINE_FLAG",
        "OPERATING_MARGIN_CONTRACTION_FLAG",
        "NET_INCOME_GROWTH_DECLINE_FLAG",
        "FINANCIAL_ANOMALY_FLAG",
    ]

    active_flags = [
        name.replace("_FLAG", "").replace("_", " ").title()
        for name in flag_names
        if latest[name] is True
    ]

    status = latest["MONITORING_STATUS"]
    indicator_count = latest["RISK_INDICATOR_COUNT"]

    flag_description = (
        ", ".join(active_flags)
        if active_flags
        else "No individual monitoring flags are active"
    )

    answer = (
        f"{latest['COMPANY_NAME']} financial monitoring status "
        f"for {latest['PERIOD_END']}: {status}. "
        f"Risk indicator count: {indicator_count}. "
        f"{flag_description}. "
        "These are financial monitoring indicators, not a predictive "
        "credit-risk or default assessment."
    )

    return {
        "status": "SUCCESS",
        "company": latest["COMPANY_NAME"],
        "latest_period": str(latest["PERIOD_END"]),
        "monitoring_status": status,
        "risk_indicator_count": indicator_count,
        "active_flags": active_flags,
        "answer_source": "SNOWFLAKE_DIRECT",
        "answer": answer
    }
