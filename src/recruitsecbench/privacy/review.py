"""Human privacy review packets and immutable review decisions."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewerRole(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


class ReviewDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


class HumanPrivacyReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    review_id: str
    derivative_id: str
    reviewer_id: str
    role: ReviewerRole
    decision: ReviewDecision
    uncertainty: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attestation_hash: str = Field(min_length=64, max_length=64)


def review_packet(derivative_id: str, analysis: object) -> dict[str, object]:
    """Export only metrics/reason codes, never raw original/derivative text."""
    return {"derivative_id": derivative_id, "analysis": getattr(analysis, "__dict__", analysis)}


def import_review(payload: dict[str, object]) -> HumanPrivacyReview:
    """Validate a human-provided review import without generating an approval."""
    return HumanPrivacyReview.model_validate(payload)
