from __future__ import annotations

import json
from pathlib import Path

import fitz

from recruitsecbench.privacy.adversarial_pdfs import (
    PDF_INJECTION_TEMPLATES,
    derive_adversarial_pdfs,
)


def test_derivatives_preserve_anonymized_pdf_structure_and_add_injection(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "redacted"
    output_dir = input_dir / "adversarial-pdfs"
    input_dir.mkdir()
    source = input_dir / "c001-redacted.pdf"
    document = fitz.open()
    first = document.new_page(width=595, height=842)
    first.insert_text((40, 60), "Anonymized professional profile")
    second = document.new_page(width=595, height=842)
    second.insert_text((40, 60), "Experience and skills")
    document.save(source)
    document.close()

    records = derive_adversarial_pdfs(input_dir=input_dir, output_dir=output_dir)

    assert len(records) == len(PDF_INJECTION_TEMPLATES) == 4
    with fitz.open(source) as original:
        original_pixels = [page.get_pixmap(alpha=False).samples for page in original]
        original_sizes = [(page.rect.width, page.rect.height) for page in original]
    for record in records:
        with fitz.open(output_dir / record["filename"]) as derived:
            assert derived.page_count == 2
            assert [(page.rect.width, page.rect.height) for page in derived] == original_sizes
            assert [page.get_pixmap(alpha=False).samples for page in derived] == original_pixels
            extracted = " ".join(page.get_text("text") for page in derived)
            assert " ".join(record["payload"].split()) in " ".join(extracted.split())

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_count"] == 1
    assert manifest["count"] == 4
    assert manifest["visual_structure_preserved"] is True
