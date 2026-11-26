
import pytest

from src.aci import monitoring
from src.aci import settings


def test_record_event_rejects_missing_credentials(monkeypatch):
    monkeypatch.setattr(settings, "SNOWFLAKE_ACCOUNT", "")
    monkeypatch.setattr(settings, "SNOWFLAKE_USER", "")
    monkeypatch.setattr(settings, "SNOWFLAKE_PASSWORD", "")

    with pytest.raises(RuntimeError, match="credentials are not configured"):
        monitoring.record_event(
            run_id="test-run",
            pipeline_name="test-pipeline",
            component="PIPELINE",
            status="RUNNING",
        )


def test_record_event_executes_merge_and_closes_connection(monkeypatch):
    monkeypatch.setattr(settings, "SNOWFLAKE_ACCOUNT", "test-account")
    monkeypatch.setattr(settings, "SNOWFLAKE_USER", "test-user")
    monkeypatch.setattr(settings, "SNOWFLAKE_PASSWORD", "test-password")

    class FakeCursor:
        def __init__(self):
            self.executed_sql = None
            self.executed_params = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def execute(self, sql, params):
            self.executed_sql = sql
            self.executed_params = params

    class FakeConnection:
        def __init__(self):
            self.fake_cursor = FakeCursor()
            self.closed = False

        def cursor(self):
            return self.fake_cursor

        def close(self):
            self.closed = True

    fake_connection = FakeConnection()

    monkeypatch.setattr(
        monitoring.snowflake.connector,
        "connect",
        lambda **kwargs: fake_connection,
    )

    monitoring.record_event(
        run_id="test-run",
        pipeline_name="test-pipeline",
        component="PIPELINE",
        status="SUCCESS",
        error_message="",
    )

    assert "MERGE INTO ACI_DB.MONITORING.PIPELINE_RUN_LOG" in (
        fake_connection.fake_cursor.executed_sql
    )
    assert fake_connection.fake_cursor.executed_params[0] == "test-run"
    assert fake_connection.fake_cursor.executed_params[3] == "SUCCESS"
    assert fake_connection.closed is True



from src.aci import pipeline


def test_pipeline_monitoring_failure_does_not_raise(monkeypatch):
    def fail_monitoring(**kwargs):
        raise RuntimeError("monitoring unavailable")

    monkeypatch.setattr(pipeline, "record_event", fail_monitoring)

    started = pipeline._start("test-run", "PIPELINE")
    pipeline._finish("test-run", "PIPELINE", started, "SUCCESS")
