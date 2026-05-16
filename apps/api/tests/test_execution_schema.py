import uuid
from datetime import UTC, datetime, timedelta, timezone

from apps.api.app.models.workflow import ExecutionLog, UTCDateTime, utc_now
from apps.api.app.schemas.execution import ExecutionLogOut, ExecutionOut


def test_execution_schema_serializes_model_aware_datetimes_as_utc():
    timestamp = datetime(2026, 5, 16, 17, 0, 1, 123000, tzinfo=UTC)
    execution = ExecutionOut(
        id=uuid.uuid4(),
        workflow_id=uuid.uuid4(),
        status="failed",
        trigger_type="manual",
        input_data={},
        output_data=None,
        started_at=timestamp,
        finished_at=timestamp,
        logs=[
            ExecutionLogOut(
                id=uuid.uuid4(),
                node_id="node-1",
                level="error",
                message="failed",
                payload=None,
                timestamp=timestamp,
            )
        ],
    )

    data = execution.model_dump(mode="json")

    assert data["started_at"] == "2026-05-16T17:00:01.123000Z"
    assert data["finished_at"] == "2026-05-16T17:00:01.123000Z"
    assert data["logs"][0]["timestamp"] == "2026-05-16T17:00:01.123000Z"


def test_execution_schema_preserves_explicit_timezone_offsets():
    timestamp = datetime(2026, 5, 16, 22, 45, tzinfo=timezone(timedelta(hours=5, minutes=45)))
    log = ExecutionLogOut(
        id=uuid.uuid4(),
        node_id="node-1",
        level="info",
        message="started",
        payload=None,
        timestamp=timestamp,
    )

    data = log.model_dump(mode="json")

    assert data["timestamp"] == "2026-05-16T22:45:00+05:45"


def test_execution_log_model_default_is_timezone_aware_utc():
    timestamp = utc_now()

    assert timestamp.tzinfo is UTC
    assert timestamp.utcoffset() == timedelta(0)
    assert isinstance(ExecutionLog.__table__.c.timestamp.type, UTCDateTime)


def test_execution_timestamp_type_reattaches_utc_to_db_naive_values():
    timestamp_type = UTCDateTime()
    stored_timestamp = datetime(2026, 5, 16, 17, 9, 30)

    timestamp = timestamp_type.process_result_value(stored_timestamp, dialect=None)

    assert timestamp == datetime(2026, 5, 16, 17, 9, 30, tzinfo=UTC)
    assert timestamp_type.process_bind_param(stored_timestamp, dialect=None) == datetime(
        2026, 5, 16, 17, 9, 30, tzinfo=UTC
    )
