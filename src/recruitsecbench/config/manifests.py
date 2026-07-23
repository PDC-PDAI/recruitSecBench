"""Content-addressed artifact manifests and atomic persistence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import AwareDatetime, Field, field_validator

from recruitsecbench.datasets.models import CanonicalModel, Partition, Sha256

DatasetName = Literal["domain", "benign", "adversarial", "deterministic", "audit"]
PrivacyReviewStatus = Literal["pending", "approved_internal", "approved_public", "restricted"]


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a JSON-compatible value using the project's canonical form."""

    if isinstance(value, CanonicalModel):
        value = value.model_dump(mode="json", exclude_none=False)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class ArtifactFile(CanonicalModel):
    path: str = Field(min_length=1)
    partition: Partition
    records: int = Field(ge=0)
    sha256: Sha256

    @field_validator("path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("artifact paths must be relative and cannot traverse parents")
        return path.as_posix()


class UpstreamManifest(CanonicalModel):
    dataset_name: DatasetName
    artifact_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    sha256: Sha256


class PrivacyReview(CanonicalModel):
    status: PrivacyReviewStatus
    reviewer_id: str | None = None
    reviewed_at: AwareDatetime | None
    notes: str | None = None


class ArtifactManifest(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    artifact_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    dataset_name: DatasetName
    record_schema: str = Field(min_length=1)
    created_at: AwareDatetime
    frozen_at: AwareDatetime | None = None
    files: list[ArtifactFile] = Field(min_length=1)
    upstream_manifests: list[UpstreamManifest] = Field(default_factory=list)
    privacy_review: PrivacyReview
    license: str = Field(min_length=1)
    notes: str | None = None

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)

    def content_sha256(self) -> str:
        return sha256_bytes(self.canonical_bytes())


class ManifestConflictError(ValueError):
    """An artifact identity was reused for different immutable content."""


class ArtifactRegistry:
    """In-memory index that refuses mutable artifact identities."""

    def __init__(self) -> None:
        self._artifacts: dict[tuple[str, str], tuple[str, ArtifactManifest]] = {}

    def register(self, manifest: ArtifactManifest) -> str:
        key = (manifest.dataset_name, manifest.artifact_version)
        digest = manifest.content_sha256()
        existing = self._artifacts.get(key)
        if existing is not None and existing[0] != digest:
            raise ManifestConflictError(
                f"artifact identity already registered with different content: {key[0]} {key[1]}"
            )
        self._artifacts[key] = (digest, manifest)
        return digest

    def get(self, dataset_name: str, artifact_version: str) -> ArtifactManifest | None:
        registered = self._artifacts.get((dataset_name, artifact_version))
        return registered[1] if registered else None

    @staticmethod
    def compatibility_issues(
        left: ArtifactManifest,
        right: ArtifactManifest,
    ) -> list[str]:
        issues: list[str] = []
        if left.dataset_name != right.dataset_name:
            issues.append("dataset_name")
        if left.schema_version != right.schema_version:
            issues.append("schema_version")
        if left.record_schema != right.record_schema:
            issues.append("record_schema")
        left_upstream = {
            (item.dataset_name, item.artifact_version): item.sha256
            for item in left.upstream_manifests
        }
        right_upstream = {
            (item.dataset_name, item.artifact_version): item.sha256
            for item in right.upstream_manifests
        }
        if left_upstream != right_upstream:
            issues.append("upstream_manifests")
        return issues


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Atomically replace a file using a temporary sibling and fsync."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_manifest_atomic(path: Path, manifest: ArtifactManifest) -> None:
    atomic_write_bytes(path, manifest.canonical_bytes() + b"\n")


def load_manifest(path: Path) -> ArtifactManifest:
    return ArtifactManifest.model_validate_json(path.read_text(encoding="utf-8"))
