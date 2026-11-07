import os
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from . import settings

def load_metrics(df: pd.DataFrame) -> int:
    required = [settings.SNOWFLAKE_ACCOUNT, settings.SNOWFLAKE_USER, settings.SNOWFLAKE_PASSWORD]
    if not all(required):
        raise ValueError("Snowflake account, user and password must be set in .env.")
    kwargs = {
        "account": settings.SNOWFLAKE_ACCOUNT,
        "user": settings.SNOWFLAKE_USER,
        "password": settings.SNOWFLAKE_PASSWORD,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        "database": settings.SNOWFLAKE_DATABASE,
        "schema": settings.SNOWFLAKE_SCHEMA,
        "login_timeout": 30,
        "network_timeout": 30,
    }
    if settings.SNOWFLAKE_ROLE:
        kwargs["role"] = settings.SNOWFLAKE_ROLE
    conn = snowflake.connector.connect(**kwargs)
    try:
        success, nchunks, nrows, output = write_pandas(
            conn, df, "FINANCIAL_METRICS", auto_create_table=False,
            quote_identifiers=False, overwrite=False
        )
        if not success:
            raise RuntimeError(f"Snowflake load failed: {output}")
        return int(nrows)
    finally:
        conn.close()
