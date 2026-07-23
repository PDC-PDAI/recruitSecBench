"""Privacy-safe structured trace events."""

from __future__ import annotations

import hashlib
import re
from datetime import timedelta
from enum import StrEnum
from typing import Any, Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from recruitsecbench.datasets.models import CanonicalId, CanonicalModel, Sha256
from recruitsecbench.validation.failures import Decision, OperationalStatus, ReasonCode
from recruitsecbench.validation.schema import validate_instance

_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d ().-]{7,}\d)(?!\d)")
_CREDENTIAL = re.compile(
    r"\b(?:api[_-]?key|password|passwd|secret|token)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_FORBIDDEN_KEYS = {
    "api_key",
    "password",
    "secret",
    "token",
    "full_prompt",
    "prompt",
    "cv_text",
    "resume_text",
    "original_text",
    "gold_label",
    "human_label",
    "human_annotations",
    "deterministic_outcome",
    "adjudication",
}


class TraceEventType(StrEnum):
    RUN_STARTED = "run_started"
    RETRIEVAL = "retrieval"
    CONTEXT_MATERIALIZED = "context_materialized"
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_REQUESTED = "tool_requested"
    POLICY_DECISION = "policy_decision"
    TOOL_COMPLETED = "tool_completed"
    STATE_TRANSITION = "state_transition"
    SIDE_EFFECT = "side_effect"
    CANARY_OBSERVATION = "canary_observation"
    ORACLE_RESULT = "oracle_result"
    AUDITOR_VIEW_CREATED = "auditor_view_created"
    AUDITOR_PREDICTION = "auditor_prediction"
    OPERATIONAL_FAILURE = "operational_failure"
    RUN_COMPLETED = "run_completed"


class TraceStage(StrEnum):
    RETRIEVAL = "retrieval"
    CONTEXT = "context"
    MODEL = "model"
    TOOL_ARGUMENT = "tool_argument"
    TOOL_RESULT = "tool_result"
    STATE = "state"
    OUTPUT = "output"
    TRACE = "trace"
    AUDITOR = "auditor"


class DataClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    IDENTITY_SCOPED = "identity_scoped"
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class Sanitization(CanonicalModel):
    profile: Literal["audit_minimal_v1", "auditor_view_v1"] = "audit_minimal_v1"
    pii_detected: Literal[False] = False
    full_prompt_stored: Literal[False] = False
    full_cv_stored: Literal[False] = False
    gold_label_included: Literal[False] = False
    redaction_count: int = Field(default=0, ge=0)


def _reject_sensitive(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = key.casefold()
            if normalized in _FORBIDDEN_KEYS or any(
                fragment in normalized
                for fragment in ("password", "secret", "credential", "api_key", "gold_label")
            ):
                raise ValueError(f"forbidden trace field: {path}.{key}")
            _reject_sensitive(nested, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive(nested, path=f"{path}[{index}]")
    elif isinstance(value, str) and (
        _EMAIL.search(value) or _PHONE.search(value) or _CREDENTIAL.search(value)
    ):
        raise ValueError(f"sensitive trace value detected at {path}")


class TracePayload(CanonicalModel):
    tool_name: str | None = Field(default=None, max_length=128)
    decision: Decision | None = None
    reason_code: ReasonCode | None = None
    status: OperationalStatus | None = None
    content_sha256: Sha256 | None = None
    content_length: int | None = Field(default=None, ge=0)
    data_classes: list[DataClass] = Field(default_factory=list)
    resource_ids: list[CanonicalId] = Field(default_factory=list)
    arguments_hash: Sha256 | None = None
    result_hash: Sha256 | None = None
    side_effect_count: int | None = Field(default=None, ge=0)
    canary_ids: list[CanonicalId] = Field(default_factory=list)
    sanitized_excerpt: str | None = Field(default=None, max_length=240)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def privacy_boundary(self) -> TracePayload:
        _reject_sensitive(self.metadata, path="payload.metadata")
        if self.sanitized_excerpt is not None:
            _reject_sensitive(self.sanitized_excerpt, path="payload.sanitized_excerpt")
        return self


class TraceEvent(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    event_id: CanonicalId
    trace_id: CanonicalId
    run_id: CanonicalId
    attempt_id: CanonicalId
    parent_event_id: CanonicalId | None = None
    sequence: int = Field(ge=0)
    timestamp: AwareDatetime
    event_type: TraceEventType
    stage: TraceStage
    actor_id: CanonicalId | None = None
    scope_hash: Sha256 | None = None
    sanitization: Sanitization
    payload: TracePayload

    @field_validator("timestamp")
    @classmethod
    def require_utc(cls, value: AwareDatetime) -> AwareDatetime:
        if value.utcoffset() != timedelta(0):
            raise ValueError("trace timestamps must be UTC")
        return value


def summarized_content(
    content: str,
    *,
    data_classes: list[DataClass | str],
) -> dict[str, Any]:
    encoded = content.encode("utf-8")
    return {
        "content_sha256": hashlib.sha256(encoded).hexdigest(),
        "content_length": len(content),
        "data_classes": data_classes,
    }


def validate_trace_schema(event: TraceEvent) -> None:
    validate_instance(
        event.model_dump(mode="json", exclude_none=True),
        "trace-event.schema.json",
        schema_root=__import__("pathlib").Path(__file__).resolve().parents[3] / "contracts",
    )
