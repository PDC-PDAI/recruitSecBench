from __future__ import annotations

from pathlib import Path

import fitz

from recruitsecbench.privacy.pdf_redaction import redact_pdf


def test_forced_header_removes_name_and_preserves_body(tmp_path: Path) -> None:
    source = tmp_path / "c005.pdf"
    output = tmp_path / "c005-redacted.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 60), "PERSONAL NAME", fontsize=20)
    page.insert_text((40, 250), "Professional experience preserved")
    document.save(source)
    document.close()

    redact_pdf(source, output)
    redacted = fitz.open(output)
    text = redacted[0].get_text("text")
    redacted.close()

    assert "PERSONAL NAME" not in text
    assert "Professional experience preserved" in text
