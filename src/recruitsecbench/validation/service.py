"""Offline schema, manifest, privacy, provenance, and compatibility gates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from recruitsecbench.config.manifests import (
    ArtifactManifest,
    ArtifactRegistry,
    ManifestConflictError,
    canonical_json_bytes,
)
from recruitsecbench.config.protocol import load_protocol
from recruitsecbench.validation.provenance import validate_manifest_provenance
from recruitsecbench.validation.schema import (
    DEFAULT_SCHEMA_ROOT,
    validate_schema_documents,
    validation_issues,
)

CheckStatus = Literal["pass", "fail"]


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    status: CheckStatus
    code: str
    message: str
    details: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class ValidationReport:
    checks: list[ValidationCheck]
    provider_calls: Literal[0] = 0

    @property
    def ok(self) -> bool:
        return all(check.status == "pass" for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.ok else "error",
            "summary": (
                "all offline validation gates passed"
                if self.ok
                else "one or more offline validation gates failed"
            ),
            "provider_calls": self.provider_calls,
            "checks": [check.as_dict() for check in self.checks],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.as_dict()) + b"\n"


@dataclass(frozen=True)
class _LoadedManifest:
    path: Path
    base_dir: Path
    manifest: ArtifactManifest


class ValidationService:
    def __init__(
        self,
        *,
        repository_root: Path,
        artifact_root: Path,
        schema_root: Path = DEFAULT_SCHEMA_ROOT,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self.artifact_root = (
            artifact_root.resolve()
            if artifact_root.is_absolute()
            else (self.repository_root / artifact_root).resolve()
        )
        self.schema_root = schema_root.resolve()

    def run(self) -> ValidationReport:
        schema_check = self._check_schemas()
        manifest_check, manifests = self._load_manifests()
        checks = [
            schema_check,
            manifest_check,
            self._check_privacy(manifests, manifest_check),
            self._check_provenance(manifests, manifest_check),
            self._check_compatibility(manifests, manifest_check),
            self._check_protocol(),
        ]
        return ValidationReport(checks=checks)

    def _check_schemas(self) -> ValidationCheck:
        details = [issue.as_dict() for issue in validate_schema_documents(self.schema_root)]
        examples_dir = self.schema_root / "examples"
        for example_path in sorted(examples_dir.glob("*.example.json")):
            schema_name = example_path.name.replace(".example.json", ".schema.json")
            try:
                instance = json.loads(example_path.read_text(encoding="utf-8"))
                details.extend(
                    issue.as_dict()
                    for issue in validation_issues(
                        instance,
                        schema_name,
                        schema_root=self.schema_root,
                    )
                )
            except (OSError, json.JSONDecodeError, ValueError) as error:
                details.append(
                    {
                        "schema_name": schema_name,
                        "instance_path": str(example_path),
                        "schema_path": "",
                        "message": str(error),
                    }
                )
        if details:
            return ValidationCheck(
                name="schemas",
                status="fail",
                code="SCHEMA_VALIDATION_FAILED",
                message="schema documents or canonical examples are invalid",
                details=details,
            )
        return ValidationCheck(
            name="schemas",
            status="pass",
            code="SCHEMAS_VALID",
            message="Draft 2020-12 schemas and canonical examples are valid",
        )

    def _manifest_paths(self) -> list[tuple[Path, Path]]:
        roots = [
            (self.repository_root / "manifests", self.repository_root),
            (self.artifact_root / "manifests", self.artifact_root),
        ]
        found: dict[Path, Path] = {}
        for manifests_dir, base_dir in roots:
            if manifests_dir.is_dir():
                for path in manifests_dir.glob("*.manifest.json"):
                    found[path.resolve()] = base_dir
        return sorted(found.items(), key=lambda item: str(item[0]))

    def _load_manifests(self) -> tuple[ValidationCheck, list[_LoadedManifest]]:
        paths = self._manifest_paths()
        if not paths:
            return (
                ValidationCheck(
                    name="manifests",
                    status="pass",
                    code="MANIFESTS_NOT_PRESENT",
                    message="no artifact manifests are present in the bootstrap workspace",
                ),
                [],
            )

        loaded: list[_LoadedManifest] = []
        details: list[dict[str, Any]] = []
        for path, base_dir in paths:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                schema_issues = validation_issues(
                    raw,
                    "manifest.schema.json",
                    schema_root=self.schema_root,
                )
                if schema_issues:
                    details.extend(
                        {"path": str(path), **issue.as_dict()} for issue in schema_issues
                    )
                    continue
                manifest = ArtifactManifest.model_validate(raw)
                loaded.append(_LoadedManifest(path=path, base_dir=base_dir, manifest=manifest))
            except (OSError, json.JSONDecodeError, ValidationError, ValueError) as error:
                issue: dict[str, Any] = {"path": str(path), "message": str(error)}
                if isinstance(error, ValidationError):
                    issue["errors"] = error.errors(include_input=False)
                details.append(issue)

        if details:
            return (
                ValidationCheck(
                    name="manifests",
                    status="fail",
                    code="MANIFEST_VALIDATION_FAILED",
                    message="one or more manifests are invalid",
                    details=details,
                ),
                loaded,
            )
        return (
            ValidationCheck(
                name="manifests",
                status="pass",
                code="MANIFESTS_VALID",
                message=f"{len(loaded)} artifact manifest(s) are structurally valid",
            ),
            loaded,
        )

    @staticmethod
    def _dependency_failed(name: str) -> ValidationCheck:
        return ValidationCheck(
            name=name,
            status="fail",
            code="MANIFEST_GATE_DEPENDENCY_FAILED",
            message="manifest validation failed; this gate cannot pass",
        )

    def _check_privacy(
        self,
        manifests: list[_LoadedManifest],
        manifest_check: ValidationCheck,
    ) -> ValidationCheck:
        if manifest_check.status == "fail":
            return self._dependency_failed("privacy_status")
        blocked = [
            {
                "path": str(item.path),
                "dataset_name": item.manifest.dataset_name,
                "status": item.manifest.privacy_review.status,
            }
            for item in manifests
            if item.manifest.privacy_review.status in {"pending", "restricted"}
        ]
        if blocked:
            return ValidationCheck(
                name="privacy_status",
                status="fail",
                code="PRIVACY_REVIEW_REQUIRED",
                message="one or more artifacts are not approved for controlled use",
                details=blocked,
            )
        return ValidationCheck(
            name="privacy_status",
            status="pass",
            code="PRIVACY_STATUS_VALID",
            message="all present artifacts have an approved privacy status",
        )

    def _check_provenance(
        self,
        manifests: list[_LoadedManifest],
        manifest_check: ValidationCheck,
    ) -> ValidationCheck:
        if manifest_check.status == "fail":
            return self._dependency_failed("provenance")
        details: list[dict[str, Any]] = []
        for item in manifests:
            details.extend(
                {"manifest": str(item.path), **issue.as_dict()}
                for issue in validate_manifest_provenance(item.manifest, item.base_dir)
            )
        if details:
            return ValidationCheck(
                name="provenance",
                status="fail",
                code="PROVENANCE_MISMATCH",
                message="artifact provenance does not match immutable manifest declarations",
                details=details,
            )
        return ValidationCheck(
            name="provenance",
            status="pass",
            code="PROVENANCE_VALID",
            message="all declared artifact bytes and record counts match",
        )

    def _check_compatibility(
        self,
        manifests: list[_LoadedManifest],
        manifest_check: ValidationCheck,
    ) -> ValidationCheck:
        if manifest_check.status == "fail":
            return self._dependency_failed("compatibility")
        registry = ArtifactRegistry()
        digests: dict[tuple[str, str], str] = {}
        details: list[dict[str, Any]] = []
        for item in manifests:
            try:
                digest = registry.register(item.manifest)
                digests[(item.manifest.dataset_name, item.manifest.artifact_version)] = digest
            except ManifestConflictError as error:
                details.append({"path": str(item.path), "message": str(error)})

        for item in manifests:
            for upstream in item.manifest.upstream_manifests:
                actual = digests.get((upstream.dataset_name, upstream.artifact_version))
                if actual != upstream.sha256:
                    details.append(
                        {
                            "path": str(item.path),
                            "dependency": f"{upstream.dataset_name}:{upstream.artifact_version}",
                            "expected_sha256": upstream.sha256,
                            "actual_sha256": actual,
                        }
                    )
        if details:
            return ValidationCheck(
                name="compatibility",
                status="fail",
                code="MANIFEST_INCOMPATIBLE",
                message="manifest identities or upstream dependencies are incompatible",
                details=details,
            )
        return ValidationCheck(
            name="compatibility",
            status="pass",
            code="MANIFESTS_COMPATIBLE",
            message="artifact identities and upstream hashes are compatible",
        )

    def _check_protocol(self) -> ValidationCheck:
        path = self.repository_root / "protocol" / "experiment.yaml"
        try:
            load_protocol(path)
        except (OSError, ValueError, ValidationError, yaml.YAMLError) as error:
            return ValidationCheck(
                name="protocol",
                status="fail",
                code="PROTOCOL_INVALID",
                message="the benchmark protocol is missing or invalid",
                details=[{"path": str(path), "message": str(error)}],
            )
        return ValidationCheck(
            name="protocol",
            status="pass",
            code="PROTOCOL_VALID",
            message="protocol identities, conditions, seeds, evidence IDs, and gates are valid",
        )
