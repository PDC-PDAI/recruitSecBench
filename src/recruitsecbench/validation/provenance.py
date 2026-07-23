"""SHA-256 provenance and immutable artifact verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from recruitsecbench.config.manifests import ArtifactManifest


@dataclass(frozen=True)
class ProvenanceIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def hash_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _jsonl_record_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as stream:
        return sum(1 for line in stream if line.strip())


def validate_manifest_provenance(
    manifest: ArtifactManifest,
    artifact_root: Path,
) -> list[ProvenanceIssue]:
    root = artifact_root.resolve()
    issues: list[ProvenanceIssue] = []
    for declared in manifest.files:
        candidate = (root / declared.path).resolve()
        if not candidate.is_relative_to(root):
            issues.append(
                ProvenanceIssue(
                    code="PROVENANCE_PATH_ESCAPE",
                    path=declared.path,
                    message="artifact path escapes the configured root",
                )
            )
            continue
        if not candidate.is_file():
            issues.append(
                ProvenanceIssue(
                    code="PROVENANCE_FILE_MISSING",
                    path=declared.path,
                    message="declared artifact file does not exist",
                )
            )
            continue
        if hash_file(candidate) != declared.sha256:
            issues.append(
                ProvenanceIssue(
                    code="PROVENANCE_HASH_MISMATCH",
                    path=declared.path,
                    message="artifact bytes do not match the manifest SHA-256",
                )
            )
            continue
        if candidate.suffix == ".jsonl" and _jsonl_record_count(candidate) != declared.records:
            issues.append(
                ProvenanceIssue(
                    code="PROVENANCE_RECORD_COUNT_MISMATCH",
                    path=declared.path,
                    message="JSONL record count does not match the manifest",
                )
            )
    return issues
