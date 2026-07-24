"""Leak scans for repository paths and sanitized trace payloads."""

from __future__ import annotations

from pathlib import Path

from recruitsecbench.privacy.analyzers import PII_PATTERNS

RESTRICTED_SUFFIXES = {".pdf", ".doc", ".docx", ".txt"}


def repository_leaks(repository_root: Path) -> list[Path]:
    """Find source-like files that are not in an explicitly ignored local directory."""
    ignored = {"pdfs", "data/derived-restricted", "data/restricted"}
    leaks: list[Path] = []
    for path in repository_root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in RESTRICTED_SUFFIXES:
            continue
        relative = path.relative_to(repository_root).as_posix()
        if any(relative == item or relative.startswith(f"{item}/") for item in ignored):
            continue
        leaks.append(path)
    return leaks


def trace_leak_categories(payload: str) -> set[str]:
    """Return categories found in a trace serialization; callers must quarantine on any hit."""
    return {name for name, pattern in PII_PATTERNS.items() if pattern.search(payload)}
