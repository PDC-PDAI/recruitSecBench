"""Restricted-source registry; source content never belongs in public artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceState(StrEnum):
    REGISTERED = "REGISTERED"
    AUTHORIZED = "AUTHORIZED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    QUARANTINED = "QUARANTINED"


class SourceDocumentRecord(BaseModel):
    """Governance metadata only; document bytes are never written to the ledger."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    source_id: str = Field(pattern=r"^[a-z][a-z0-9-]{2,127}$")
    relative_path: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    origin: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    controller: str = Field(min_length=1)
    responsible_person: str = Field(min_length=1)
    legal_basis: str = Field(min_length=1)
    authorization_evidence: str = Field(min_length=1)
    privacy_approved: bool
    retention_until: date
    revocation_policy: str = Field(min_length=1)
    state: SourceState = SourceState.REGISTERED
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def governance_is_complete(self) -> SourceDocumentRecord:
        if self.state is SourceState.AUTHORIZED and not self.privacy_approved:
            raise ValueError("an authorized source requires privacy approval")
        return self

    def usable(self, today: date | None = None) -> bool:
        return (
            self.state is SourceState.AUTHORIZED
            and self.privacy_approved
            and self.retention_until >= (today or date.today())
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class RestrictedSourceRegistry:
    """JSON metadata ledger for sources held locally or outside the worktree."""

    def __init__(self, ledger: Path, *, repository_root: Path) -> None:
        self.ledger = ledger.resolve()
        self.repository_root = repository_root.resolve()

    def _inside_repository(self, path: Path) -> bool:
        try:
            path.relative_to(self.repository_root)
        except ValueError:
            return False
        return True

    def _git_ignored(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.repository_root).as_posix()
        except ValueError:
            return True
        ignore_file = self.repository_root / ".gitignore"
        if not ignore_file.is_file():
            return False
        patterns = {
            line.strip().rstrip("/")
            for line in ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("!")
        }
        return any(
            relative == pattern or relative.startswith(f"{pattern}/") for pattern in patterns
        )

    def register(self, raw_path: Path, **metadata: object) -> SourceDocumentRecord:
        resolved = raw_path.resolve()
        if self._inside_repository(resolved) and not self._git_ignored(resolved):
            raise ValueError("raw source must be Git-ignored when kept in the repository")
        if not resolved.is_file():
            raise ValueError("raw source document does not exist")
        source = SourceDocumentRecord(
            relative_path=str(resolved), content_sha256=sha256_file(resolved), **metadata
        )
        records = self.load()
        if any(item.source_id == source.source_id for item in records):
            raise ValueError(f"source already registered: {source.source_id}")
        records.append(source)
        self.save(records)
        return source

    def load(self) -> list[SourceDocumentRecord]:
        if not self.ledger.exists():
            return []
        return [
            SourceDocumentRecord.model_validate(item)
            for item in json.loads(self.ledger.read_text())
        ]

    def save(self, records: list[SourceDocumentRecord]) -> None:
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.model_dump(mode="json") for item in records]
        temporary = self.ledger.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        temporary.replace(self.ledger)
