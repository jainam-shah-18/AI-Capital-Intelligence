import os
from pathlib import Path

from dotenv import dotenv_values
import snowflake.connector
from snowflake.connector import DictCursor


APPROVED_MARTS = {
    "MART_COMPANY_PERFORMANCE",
    "MART_COMPANY_COMPARISON",
    "MART_REVENUE_FORECAST",
    "MART_CASH_FLOW_ANALYSIS",
    "MART_FINANCIAL_ANOMALIES",
    "MART_FINANCIAL_RISK_INDICATORS",
}


def get_connection():
    env = dotenv_values(Path(__file__).resolve().parents[2] / ".env")

    required = [
        "ACI_AI_SNOWFLAKE_ACCOUNT",
        "ACI_AI_SNOWFLAKE_USER",
        "ACI_AI_SNOWFLAKE_TOKEN",
        "ACI_AI_SNOWFLAKE_WAREHOUSE",
        "ACI_AI_SNOWFLAKE_DATABASE",
        "ACI_AI_SNOWFLAKE_SCHEMA",
        "ACI_AI_SNOWFLAKE_ROLE",
        "ACI_AI_SNOWFLAKE_AUTHENTICATOR",
    ]

    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError(
            "Missing AI Snowflake configuration: " + ", ".join(missing)
        )

    return snowflake.connector.connect(
        account=env["ACI_AI_SNOWFLAKE_ACCOUNT"],
        user=env["ACI_AI_SNOWFLAKE_USER"],
        token=env["ACI_AI_SNOWFLAKE_TOKEN"],
        authenticator=env["ACI_AI_SNOWFLAKE_AUTHENTICATOR"],
        warehouse=env["ACI_AI_SNOWFLAKE_WAREHOUSE"],
        database=env["ACI_AI_SNOWFLAKE_DATABASE"],
        schema=env["ACI_AI_SNOWFLAKE_SCHEMA"],
        role=env["ACI_AI_SNOWFLAKE_ROLE"],
    )


def fetch_mart_rows(mart_name: str, limit: int = 100) -> list[dict]:
    mart_name = mart_name.upper().strip()

    if mart_name not in APPROVED_MARTS:
        raise ValueError("This financial mart is not approved for retrieval.")

    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise ValueError("Limit must be an integer between 1 and 500.")

    env = dotenv_values(Path(__file__).resolve().parents[2] / ".env")
    database = env["ACI_AI_SNOWFLAKE_DATABASE"]
    schema = env["ACI_AI_SNOWFLAKE_SCHEMA"]

    # Database and schema come from local configuration, not user or LLM input.
    sql = (
        f"SELECT * FROM {database}.{schema}.{mart_name} "
        f"LIMIT {limit}"
    )

    conn = get_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def test_connection() -> dict:
    conn = get_connection()
    try:
        with conn.cursor(DictCursor) as cursor:
            cursor.execute("""
                SELECT
                    CURRENT_USER() AS CURRENT_USER,
                    CURRENT_ROLE() AS CURRENT_ROLE,
                    CURRENT_DATABASE() AS CURRENT_DATABASE,
                    CURRENT_SCHEMA() AS CURRENT_SCHEMA,
                    CURRENT_WAREHOUSE() AS CURRENT_WAREHOUSE
            """)
            return cursor.fetchone()
    finally:
        conn.close()