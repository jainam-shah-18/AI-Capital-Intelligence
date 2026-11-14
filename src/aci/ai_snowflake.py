import re
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


def _configuration():
    env = dotenv_values(Path(__file__).resolve().parents[2] / ".env")

    config = {
        "account": env.get("SNOWFLAKE_ACCOUNT"),
        "user": env.get("SNOWFLAKE_USER"),
        "password": env.get("SNOWFLAKE_PASSWORD"),
        "warehouse": env.get("SNOWFLAKE_WAREHOUSE"),
        "database": env.get("SNOWFLAKE_DATABASE"),
        "schema": env.get("ACI_AI_SNOWFLAKE_SCHEMA") or "DBT_DEV",
        "role": env.get("SNOWFLAKE_ROLE"),
    }

    missing = [
        key for key, value in config.items()
        if key != "role" and not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Snowflake configuration: " + ", ".join(missing)
        )

    for key in ("database", "schema"):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", config[key]):
            raise ValueError(f"Invalid Snowflake {key} identifier.")

    return config


def get_connection():
    config = _configuration()
    if not config["role"]:
        config.pop("role")
    return snowflake.connector.connect(**config)


def fetch_mart_rows(mart_name: str, limit: int = 100) -> list[dict]:
    mart_name = mart_name.upper().strip()

    if mart_name not in APPROVED_MARTS:
        raise ValueError("This financial mart is not approved for retrieval.")

    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise ValueError("Limit must be an integer between 1 and 500.")

    config = _configuration()
    sql = (
        f"SELECT * FROM {config['database']}."
        f"{config['schema']}.{mart_name} LIMIT {limit}"
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
