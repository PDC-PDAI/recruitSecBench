from __future__ import annotations

from pathlib import Path

from recruitsecbench.privacy.scans import repository_leaks, trace_leak_categories


def test_trace_scan_detects_email_without_retaining_content() -> None:
    assert trace_leak_categories("event contact candidate@example.com") == {"email"}


def test_repository_scan_allows_explicit_restricted_directories(tmp_path: Path) -> None:
    allowed = tmp_path / "pdfs"
    allowed.mkdir()
    (allowed / "source.pdf").write_bytes(b"source")
    exposed = tmp_path / "notes.txt"
    exposed.write_text("source", encoding="utf-8")
    assert repository_leaks(tmp_path) == [exposed]
