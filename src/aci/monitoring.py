import snowflake.connector
from . import settings


def record_event(
    run_id,
    pipeline_name,
    component,
    status,
    started_at=None,
    finished_at=None,
    duration_seconds=None,
    rows_extracted=None,
    rows_loaded=None,
    source_name=None,
    target_name=None,
    error_message=None,
):
    if not all([
        settings.SNOWFLAKE_ACCOUNT,
        settings.SNOWFLAKE_USER,
        settings.SNOWFLAKE_PASSWORD,
    ]):
        raise RuntimeError("Snowflake monitoring credentials are not configured.")

    kwargs = {
        "account": settings.SNOWFLAKE_ACCOUNT,
        "user": settings.SNOWFLAKE_USER,
        "password": settings.SNOWFLAKE_PASSWORD,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        "database": "ACI_DB",
        "schema": "MONITORING",
        "login_timeout": 30,
        "network_timeout": 30,
    }

    if settings.SNOWFLAKE_ROLE:
        kwargs["role"] = settings.SNOWFLAKE_ROLE

    sql = """
        MERGE INTO ACI_DB.MONITORING.PIPELINE_RUN_LOG t
        USING (
            SELECT
                %s AS RUN_ID,
                %s AS PIPELINE_NAME,
                %s AS COMPONENT,
                %s AS STATUS,
                %s AS STARTED_AT,
                %s AS FINISHED_AT,
                %s AS DURATION_SECONDS,
                %s AS ROWS_EXTRACTED,
                %s AS ROWS_LOADED,
                %s AS SOURCE_NAME,
                %s AS TARGET_NAME,
                %s AS ERROR_MESSAGE
        ) s
        ON t.RUN_ID = s.RUN_ID
        AND t.PIPELINE_NAME = s.PIPELINE_NAME
        AND t.COMPONENT = s.COMPONENT

        WHEN MATCHED THEN UPDATE SET
            STATUS = s.STATUS,
            STARTED_AT = s.STARTED_AT,
            FINISHED_AT = s.FINISHED_AT,
            DURATION_SECONDS = s.DURATION_SECONDS,
            ROWS_EXTRACTED = s.ROWS_EXTRACTED,
            ROWS_LOADED = s.ROWS_LOADED,
            SOURCE_NAME = s.SOURCE_NAME,
            TARGET_NAME = s.TARGET_NAME,
            ERROR_MESSAGE = s.ERROR_MESSAGE

        WHEN NOT MATCHED THEN INSERT (
            RUN_ID, PIPELINE_NAME, COMPONENT, STATUS,
            STARTED_AT, FINISHED_AT, DURATION_SECONDS,
            ROWS_EXTRACTED, ROWS_LOADED,
            SOURCE_NAME, TARGET_NAME, ERROR_MESSAGE
        )
        VALUES (
            s.RUN_ID, s.PIPELINE_NAME, s.COMPONENT, s.STATUS,
            s.STARTED_AT, s.FINISHED_AT, s.DURATION_SECONDS,
            s.ROWS_EXTRACTED, s.ROWS_LOADED,
            s.SOURCE_NAME, s.TARGET_NAME, s.ERROR_MESSAGE
        )
    """

    conn = snowflake.connector.connect(**kwargs)

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (
                run_id,
                pipeline_name,
                component,
                status,
                started_at,
                finished_at,
                duration_seconds,
                rows_extracted,
                rows_loaded,
                source_name,
                target_name,
                str(error_message)[:4000] if error_message else None,
            ))
    finally:
        conn.close()
