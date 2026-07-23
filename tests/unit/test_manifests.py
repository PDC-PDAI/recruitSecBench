from __future__ import annotations

import json

from recruitsecbench.config.manifests import (
    ArtifactFile,
    ArtifactManifest,
    ArtifactRegistry,
    PrivacyReview,
    UpstreamManifest,
    write_manifest_atomic,
)
from recruitsecbench.datasets.models import Partition
from recruitsecbench.validation.provenance import hash_file, validate_manifest_provenance


def _manifest(file_hash: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_version="0.1.0",
        dataset_name="domain",
        record_schema="domain.schema.json",
        created_at="2026-07-22T12:00:00Z",
        files=[
            ArtifactFile(
                path="domain/development.jsonl",
                partition=Partition.DEVELOPMENT,
                records=1,
                sha256=file_hash,
            )
        ],
        upstream_manifests=[
            UpstreamManifest(
                dataset_name="deterministic", artifact_version="0.1.0", sha256="b" * 64
            )
        ],
        privacy_review=PrivacyReview(status="approved_public", reviewed_at="2026-07-22T12:00:00Z"),
        license="MIT",
    )


def test_manifest_digest_and_atomic_write_are_deterministic(tmp_path) -> None:
    artifact = tmp_path / "domain" / "development.jsonl"
    artifact.parent.mkdir()
    artifact.write_text('{"record_id":"one"}\n', encoding="utf-8")
    manifest = _manifest(hash_file(artifact))

    first = manifest.content_sha256()
    second = ArtifactManifest.model_validate(manifest.model_dump(mode="json")).content_sha256()
    assert first == second

    destination = tmp_path / "domain.manifest.json"
    write_manifest_atomic(destination, manifest)
    loaded = json.loads(destination.read_text(encoding="utf-8"))
    assert loaded["dataset_name"] == "domain"
    assert not list(tmp_path.glob("*.tmp"))


def test_provenance_detects_mutated_artifacts(tmp_path) -> None:
    artifact = tmp_path / "domain" / "development.jsonl"
    artifact.parent.mkdir()
    artifact.write_text('{"record_id":"one"}\n', encoding="utf-8")
    manifest = _manifest(hash_file(artifact))

    assert validate_manifest_provenance(manifest, tmp_path) == []

    artifact.write_text('{"record_id":"mutated"}\n', encoding="utf-8")
    issues = validate_manifest_provenance(manifest, tmp_path)
    assert [issue.code for issue in issues] == ["PROVENANCE_HASH_MISMATCH"]


def test_registry_rejects_incompatible_identity() -> None:
    registry = ArtifactRegistry()
    original = _manifest("a" * 64)
    registry.register(original)

    changed = original.model_copy(update={"record_schema": "domain-v2.schema.json"})
    issues = registry.compatibility_issues(original, changed)

    assert "record_schema" in issues
