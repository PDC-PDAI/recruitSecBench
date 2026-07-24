from __future__ import annotations

from pathlib import Path

import fitz

from recruitsecbench.privacy.pdf_redaction import redact_pdf, unresolved_right_column_names


def test_redaction_removes_right_column_name_and_direct_identifier(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "redacted.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 60), "Professional experience")
    page.insert_text((330, 60), "Jane Doe")
    page.insert_text((330, 80), "jane@example.com")
    document.save(source)
    document.close()

    counts = redact_pdf(source, output)
    redacted = fitz.open(output)
    text = redacted[0].get_text("text")
    redacted.close()

    assert counts.get("name", 0) + counts.get("right_column_name", 0) >= 1
    assert counts["email"] == 1
    assert "Jane Doe" not in text
    assert "jane@example.com" not in text
    assert unresolved_right_column_names(output) == 0
