"""Stable decisions, reason codes, and operational failure taxonomy."""

from __future__ import annotations

from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ERROR = "ERROR"


class ReasonCode(StrEnum):
    ACTOR_UNAUTHENTICATED = "ACTOR_UNAUTHENTICATED"
    ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"
    TOOL_NOT_ALLOWED = "TOOL_NOT_ALLOWED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    ID_ALIAS_CONFLICT = "ID_ALIAS_CONFLICT"
    ID_BINDING_INVALID = "ID_BINDING_INVALID"
    CROSS_SCOPE_ACCESS = "CROSS_SCOPE_ACCESS"
    ARGUMENT_SCHEMA_INVALID = "ARGUMENT_SCHEMA_INVALID"
    STATE_TRANSITION_INVALID = "STATE_TRANSITION_INVALID"
    ROUND_TOKEN_STALE = "ROUND_TOKEN_STALE"  # nosec B105
    DUPLICATE_EFFECT = "DUPLICATE_EFFECT"
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    INTEGRITY_FLOW_BLOCKED = "INTEGRITY_FLOW_BLOCKED"
    CONFIDENTIALITY_FLOW_BLOCKED = "CONFIDENTIALITY_FLOW_BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    HARNESS_ERROR = "HARNESS_ERROR"
    ADAPTER_CONTRACT_MISMATCH = "ADAPTER_CONTRACT_MISMATCH"
    MANIFEST_INCOMPATIBLE = "MANIFEST_INCOMPATIBLE"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    PRIVACY_REVIEW_REQUIRED = "PRIVACY_REVIEW_REQUIRED"
    PROVENANCE_MISMATCH = "PROVENANCE_MISMATCH"


class OperationalStatus(StrEnum):
    COMPLETED = "completed"
    PROVIDER_ERROR = "provider_error"
    TRANSPORT_ERROR = "transport_error"
    HARNESS_ERROR = "harness_error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BUDGET_BLOCKED = "budget_blocked"
    INVALID_CASE = "invalid_case"
    INCONCLUSIVE = "inconclusive"

    @property
    def is_scientific_outcome(self) -> bool:
        return self is OperationalStatus.COMPLETED

    @property
    def retryable(self) -> bool:
        return self in {
            OperationalStatus.PROVIDER_ERROR,
            OperationalStatus.TRANSPORT_ERROR,
            OperationalStatus.HARNESS_ERROR,
            OperationalStatus.TIMEOUT,
            OperationalStatus.CANCELLED,
        }
