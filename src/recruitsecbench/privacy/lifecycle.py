"""Quarantine, revocation, and minimal technical tombstones."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from recruitsecbench.privacy.sources import SourceDocumentRecord, SourceState


class Tombstone(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    derivative_id: str | None = None
    reason: str = Field(min_length=1)
    effective_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tombstone_hash: str


def quarantine(
    source: SourceDocumentRecord, *, reason: str, derivative_id: str | None = None
) -> Tombstone:
    """Invalidate a source without retaining its content or detailed evidence."""
    source.state = SourceState.QUARANTINED
    stamp = datetime.now(UTC)
    digest = hashlib.sha256(
        f"{source.source_id}|{derivative_id}|{reason}|{stamp.isoformat()}".encode()
    ).hexdigest()
    return Tombstone(
        source_id=source.source_id,
        derivative_id=derivative_id,
        reason=reason,
        effective_at=stamp,
        tombstone_hash=digest,
    )


def revoke(
    source: SourceDocumentRecord, *, reason: str, derivative_id: str | None = None
) -> Tombstone:
    tombstone = quarantine(source, reason=reason, derivative_id=derivative_id)
    source.state = SourceState.REVOKED
    return tombstone
