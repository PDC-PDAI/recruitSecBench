from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from recruitsecbench.privacy.lifecycle import quarantine, revoke
from recruitsecbench.privacy.sources import RestrictedSourceRegistry, SourceState


def _metadata() -> dict[str, object]:
    return {
        "source_id": "source-001",
        "origin": "authorized archive",
        "purpose": "restricted curation",
        "controller": "controller-001",
        "responsible_person": "owner-001",
        "legal_basis": "consent",
        "authorization_evidence": "consent-ref-001",
        "privacy_approved": True,
        "retention_until": date.today() + timedelta(days=30),
        "revocation_policy": "quarantine immediately",
        "state": SourceState.AUTHORIZED,
    }


def test_registry_rejects_unignored_sources_inside_repository(tmp_path: Path) -> None:
    raw = tmp_path / "raw.pdf"
    raw.write_bytes(b"not a real PDF")
    registry = RestrictedSourceRegistry(
        tmp_path / "restricted" / "ledger.json", repository_root=tmp_path
    )
    with pytest.raises(ValueError, match="Git-ignored"):
        registry.register(raw, **_metadata())


def test_registry_and_lifecycle_keep_only_tombstone_metadata(tmp_path: Path) -> None:
    restricted = tmp_path / "restricted"
    raw = restricted / "source.txt"
    restricted.mkdir()
    raw.write_text("private CV text", encoding="utf-8")
    registry = RestrictedSourceRegistry(
        restricted / "ledger.json", repository_root=tmp_path / "repo"
    )
    source = registry.register(raw, **_metadata())
    assert registry.load()[0].content_sha256 == source.content_sha256
    tombstone = quarantine(source, reason="PII_DETECTED", derivative_id="derived-001")
    assert source.state is SourceState.QUARANTINED
    assert "private CV text" not in tombstone.model_dump_json()
    revoke(source, reason="CONSENT_REVOKED")
    assert source.state is SourceState.REVOKED
