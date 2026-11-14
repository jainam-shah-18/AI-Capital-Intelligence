
from snowflake.connector import DictCursor

from src.aci.ai_snowflake import get_connection


COMPANY_NAMES = {
    "amazon.com, inc.": "AMAZON.COM, INC.",
    "alphabet inc.": "Alphabet Inc.",
    "microsoft corporation": "MICROSOFT CORPORATION",
    "meta platforms, inc.": "Meta Platforms, Inc.",
}


def validate_company_and_limit(
    company_name: str,
    limit: int
) -> str:
    """Validate company name and retrieval limit."""

    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("A valid company name is required.")

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
    ):
        raise ValueError("Limit must be an integer between 1 and 100.")

    canonical_name = COMPANY_NAMES.get(company_name.strip().lower())

    if canonical_name is None:
        raise ValueError(
            "Company is not available in the financial database."
        )

    return canonical_name


def retrieve_company_performance(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve recent financial performance records."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            PERIOD_START,
            PERIOD_END,
            DURATION_CLASS,
            FILING_FISCAL_YEAR,
            FILING_FISCAL_PERIOD,
            REVENUE,
            OPERATING_INCOME,
            NET_INCOME,
            OPERATING_CASH_FLOW,
            CAPEX,
            FREE_CASH_FLOW,
            OPERATING_MARGIN_PCT,
            NET_PROFIT_MARGIN_PCT,
            REVENUE_QOQ_GROWTH_PCT,
            REVENUE_YOY_GROWTH_PCT
        FROM ACI_DB.DBT_DEV.MART_COMPANY_PERFORMANCE
        WHERE COMPANY_NAME = %s
        ORDER BY PERIOD_END DESC
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def retrieve_company_comparison(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve peer comparison and company ranking records."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            PERIOD_START,
            PERIOD_END,
            CALENDAR_YEAR,
            CALENDAR_QUARTER,
            REVENUE,
            OPERATING_INCOME,
            NET_INCOME,
            OPERATING_MARGIN_PCT,
            NET_PROFIT_MARGIN_PCT,
            REVENUE_YOY_GROWTH_PCT,
            PEER_AVG_REVENUE,
            PEER_AVG_OPERATING_MARGIN_PCT,
            PEER_AVG_NET_PROFIT_MARGIN_PCT,
            REVENUE_SHARE_PCT,
            REVENUE_RANK,
            OPERATING_INCOME_RANK,
            NET_INCOME_RANK,
            COMPARISON_COMPANY_COUNT
        FROM ACI_DB.DBT_DEV.MART_COMPANY_COMPARISON
        WHERE COMPANY_NAME = %s
        ORDER BY PERIOD_END DESC
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def retrieve_cash_flow(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve cash-flow analysis records."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            UNIT,
            PERIOD_START,
            PERIOD_END,
            FILING_FISCAL_YEAR,
            FILING_FISCAL_PERIOD,
            OPERATING_CASH_FLOW,
            CAPEX_REPORTED_VALUE,
            CAPEX_CONCEPT_COUNT,
            CAPEX_CONCEPT_NAME,
            CAPEX_REPORTING_BASIS,
            FREE_CASH_FLOW,
            FREE_CASH_FLOW_STATUS,
            CAPEX_QUALITY_STATUS
        FROM ACI_DB.DBT_DEV.MART_CASH_FLOW_ANALYSIS
        WHERE COMPANY_NAME = %s
        ORDER BY PERIOD_END DESC
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def retrieve_revenue_forecast(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve actual and forecast revenue records."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            FISCAL_CALENDAR_TYPE,
            FORECAST_RECORD_TYPE,
            TARGET_FISCAL_YEAR,
            TARGET_FISCAL_QUARTER,
            TARGET_PERIOD_START,
            TARGET_PERIOD_END,
            ACTUAL_PERIOD_END,
            FORECAST_SOURCE_PERIOD_END,
            ACTUAL_REVENUE,
            FORECAST_REVENUE,
            FORECAST_ERROR,
            ABSOLUTE_ERROR,
            ABSOLUTE_PERCENTAGE_ERROR
        FROM ACI_DB.DBT_DEV.MART_REVENUE_FORECAST
        WHERE COMPANY_NAME = %s
        ORDER BY TARGET_PERIOD_END DESC, FORECAST_RECORD_TYPE
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def retrieve_financial_anomalies(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve financial anomaly detection records."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            METRIC_NAME,
            CONCEPT_NAME,
            UNIT,
            PERIOD_START,
            PERIOD_END,
            CURRENT_VALUE,
            PRIOR_YEAR_VALUE,
            COMPARISON_QUALITY_STATUS,
            YOY_GROWTH_PCT,
            HISTORICAL_OBSERVATION_COUNT,
            HISTORICAL_AVG_YOY_GROWTH_PCT,
            HISTORICAL_STDDEV_YOY_GROWTH_PCT,
            ANOMALY_Z_SCORE,
            ANOMALY_STATUS,
            ANOMALY_DIRECTION,
            ANOMALY_THRESHOLD_STANDARD_DEVIATIONS
        FROM ACI_DB.DBT_DEV.MART_FINANCIAL_ANOMALIES
        WHERE COMPANY_NAME = %s
        ORDER BY PERIOD_END DESC
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def retrieve_financial_risk(
    company_name: str,
    limit: int = 8
) -> list[dict]:
    """Retrieve financial risk monitoring indicators."""

    canonical_name = validate_company_and_limit(company_name, limit)

    sql = """
        SELECT
            COMPANY_NAME,
            PERIOD_START,
            PERIOD_END,
            REVENUE,
            REVENUE_YOY_GROWTH_PCT,
            OPERATING_INCOME,
            OPERATING_MARGIN,
            OPERATING_MARGIN_CHANGE_PP,
            OPERATING_INCOME_YOY_GROWTH_PCT,
            NET_INCOME,
            NET_INCOME_YOY_GROWTH_PCT,
            ANOMALY_OBSERVATION_COUNT,
            FLAGGED_ANOMALY_COUNT,
            REVENUE_GROWTH_DECLINE_FLAG,
            OPERATING_MARGIN_CONTRACTION_FLAG,
            NET_INCOME_GROWTH_DECLINE_FLAG,
            FINANCIAL_ANOMALY_FLAG,
            RISK_INDICATOR_COUNT,
            MONITORING_STATUS
        FROM ACI_DB.DBT_DEV.MART_FINANCIAL_RISK_INDICATORS
        WHERE COMPANY_NAME = %s
        ORDER BY PERIOD_END DESC
        LIMIT %s
    """

    conn = get_connection()

    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql, (canonical_name, limit))
            return cursor.fetchall()
    finally:
        conn.close()
