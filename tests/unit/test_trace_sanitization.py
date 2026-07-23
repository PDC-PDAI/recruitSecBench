from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from recruitsecbench.privacy.traces import (
    Sanitization,
    TraceEvent,
    TraceEventType,
    TracePayload,
    TraceStage,
    summarized_content,
    validate_trace_schema,
)
from recruitsecbench.validation.failures import OperationalStatus, ReasonCode


def _event(payload: TracePayload) -> TraceEvent:
    return TraceEvent(
        event_id="event-001",
        trace_id="trace-001",
        run_id="run-001",
        attempt_id="attempt-001",
        sequence=0,
        timestamp="2026-07-22T12:00:00Z",
        event_type=TraceEventType.MODEL_RESPONSE,
        stage=TraceStage.MODEL,
        sanitization=Sanitization(),
        payload=payload,
    )


def test_trace_stores_hash_and_length_instead_of_raw_content() -> None:
    summary = summarized_content("safe synthetic content", data_classes=["untrusted"])
    event = _event(TracePayload(**summary))

    dumped = event.model_dump(mode="json", exclude_none=True)
    assert dumped["payload"]["content_length"] == 22
    assert "safe synthetic content" not in json.dumps(dumped)
    validate_trace_schema(event)


def test_trace_rejects_sensitive_metadata_and_pii_excerpt() -> None:
    with pytest.raises(ValidationError):
        _event(TracePayload(metadata={"api_key": "secret-value"}))

    with pytest.raises(ValidationError):
        _event(TracePayload(sanitized_excerpt="contact candidate@example.com"))


def test_reason_codes_and_operational_failures_are_stable_and_separate() -> None:
    assert ReasonCode.CROSS_SCOPE_ACCESS.value == "CROSS_SCOPE_ACCESS"
    assert OperationalStatus.PROVIDER_ERROR.value == "provider_error"
    assert OperationalStatus.PROVIDER_ERROR.is_scientific_outcome is False
    assert OperationalStatus.COMPLETED.is_scientific_outcome is True
