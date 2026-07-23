from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecruitSecBenchFailure(Exception):
    """Base failure with a public message and contract-defined exit status."""

    message: str
    exit_code: int
    details: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message


class ConfigurationFailure(RecruitSecBenchFailure):
    """Invalid command options or non-secret configuration."""

    def __init__(self, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message=message, exit_code=2, details=details or [])
