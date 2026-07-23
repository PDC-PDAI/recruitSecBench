"""Offline JSON Schema Draft 2020-12 validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA_ROOT = REPOSITORY_ROOT / "schemas"


@dataclass(frozen=True)
class SchemaIssue:
    schema_name: str
    instance_path: str
    schema_path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "schema_name": self.schema_name,
            "instance_path": self.instance_path,
            "schema_path": self.schema_path,
            "message": self.message,
        }


class SchemaValidationFailure(ValueError):
    """One or more deterministic schema validation failures."""

    def __init__(self, issues: list[SchemaIssue]) -> None:
        self.issues = issues
        super().__init__(f"schema validation failed with {len(issues)} issue(s)")


def _json_pointer(parts: Any) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else ""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"schema must be a JSON object: {path}")
    return payload


def schema_registry(schema_root: Path = DEFAULT_SCHEMA_ROOT) -> Registry:
    registry: Registry = Registry()
    for path in sorted(schema_root.glob("*.schema.json")):
        contents = _load_json(path)
        resource = Resource.from_contents(contents)
        registry = registry.with_resource(path.name, resource)
        identifier = contents.get("$id")
        if isinstance(identifier, str):
            registry = registry.with_resource(identifier, resource)
    return registry


def validator_for(
    schema_name: str,
    *,
    schema_root: Path = DEFAULT_SCHEMA_ROOT,
) -> Draft202012Validator:
    schema_path = schema_root / schema_name
    schema = _load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(
        schema,
        registry=schema_registry(schema_root),
        format_checker=FormatChecker(),
    )


def validation_issues(
    instance: Any,
    schema_name: str,
    *,
    schema_root: Path = DEFAULT_SCHEMA_ROOT,
) -> list[SchemaIssue]:
    validator = validator_for(schema_name, schema_root=schema_root)
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: (_json_pointer(error.absolute_path), error.message),
    )
    return [
        SchemaIssue(
            schema_name=schema_name,
            instance_path=_json_pointer(error.absolute_path),
            schema_path=_json_pointer(error.absolute_schema_path),
            message=error.message,
        )
        for error in errors
    ]


def validate_instance(
    instance: Any,
    schema_name: str,
    *,
    schema_root: Path = DEFAULT_SCHEMA_ROOT,
) -> None:
    issues = validation_issues(instance, schema_name, schema_root=schema_root)
    if issues:
        raise SchemaValidationFailure(issues)


def validate_schema_documents(schema_root: Path = DEFAULT_SCHEMA_ROOT) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []
    for path in sorted(schema_root.glob("*.schema.json")):
        try:
            Draft202012Validator.check_schema(_load_json(path))
        except (SchemaError, ValueError, json.JSONDecodeError) as error:
            issues.append(
                SchemaIssue(
                    schema_name=path.name,
                    instance_path="",
                    schema_path="",
                    message=str(error),
                )
            )
    return issues