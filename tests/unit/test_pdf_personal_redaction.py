from __future__ import annotations

from pathlib import Path

import fitz

from recruitsecbench.privacy.pdf_redaction import redact_pdf, unresolved_personal_fields


def test_redaction_removes_single_header_name_contact_and_link(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "redacted.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((330, 45), "Mariana", fontsize=22)
    page.insert_text((330, 75), "linkedin.com/in/mariana")
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(330, 62, 500, 82),
            "uri": "https://linkedin.com/in/mariana",
        }
    )
    document.save(source)
    document.close()

    redact_pdf(source, output)
    redacted = fitz.open(output)
    text = redacted[0].get_text("text")
    links = redacted[0].get_links()
    redacted.close()

    assert "Mariana" not in text
    assert "linkedin.com" not in text
    assert links == []
    assert unresolved_personal_fields(output) == {"names": 0, "contacts": 0, "links": 0}
