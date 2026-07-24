"""Local PDF redaction preserving source page geometry for human-review drafts."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz

DIRECT_PATTERNS = (
    ("email", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL REMOVED]"),
    ("phone", re.compile(r"\b(?:\+?\d[\d .()-]{7,}\d)\b"), "[PHONE REMOVED]"),
    ("url", re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE), "[URL REMOVED]"),
    ("document", re.compile(r"\b\d{3}[. -]?\d{3}[. -]?\d{3}[- ]?\d{2}\b"), "[ID REMOVED]"),
)
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
CONTACT_HINTS = {
    "address",
    "contact",
    "contato",
    "cpf",
    "email",
    "endereco",
    "github",
    "linkedin",
    "phone",
    "telefone",
    "whatsapp",
}
NON_NAME_LINES = {
    "academic background",
    "certifications",
    "competencias",
    "competencies",
    "dados pessoais",
    "education",
    "experiencia profissional",
    "formacao academica",
    "idiomas",
    "languages",
    "personal details",
    "professional experience",
    "professional summary",
    "resumo profissional",
    "skills",
}
REDACTION_MARKERS = {
    "contact removed",
    "email removed",
    "id removed",
    "name removed",
    "personal details removed",
    "phone removed",
    "url removed",
}
FORCED_HEADER_REDACTION = {"c005", "c026", "c045", "c047"}


def is_name_like(value: str) -> bool:
    words = WORD.findall(value.strip())
    normalized = " ".join(words).casefold()
    if (
        not words
        or len(words) > 5
        or normalized in NON_NAME_LINES | REDACTION_MARKERS
        or any(marker in normalized for marker in REDACTION_MARKERS)
    ):
        return False
    return all(word.isupper() or (word[0].isupper() and word[1:].islower()) for word in words)


def _line_records(page: fitz.Page) -> list[tuple[str, fitz.Rect]]:
    grouped: dict[tuple[int, int], list[tuple[float, float, float, float, str]]] = {}
    for x0, y0, x1, y1, word, block, line, *_ in page.get_text("words"):
        grouped.setdefault((block, line), []).append((x0, y0, x1, y1, word))
    records = []
    for words in grouped.values():
        ordered = sorted(words)
        records.append(
            (
                " ".join(item[4] for item in ordered),
                fitz.Rect(
                    min(item[0] for item in ordered) - 1,
                    min(item[1] for item in ordered) - 1,
                    max(item[2] for item in ordered) + 1,
                    max(item[3] for item in ordered) + 1,
                ),
            )
        )
    return records


def _top_name_rects(page: fitz.Page) -> list[fitz.Rect]:
    candidates: list[tuple[float, fitz.Rect]] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                rect = fitz.Rect(span["bbox"])
                if rect.y0 <= page.rect.height * 0.32 and is_name_like(text):
                    candidates.append((float(span["size"]), rect + (-1, -1, 1, 1)))
    if not candidates:
        return []
    largest = max(item[0] for item in candidates)
    return [rect for size, rect in candidates if size >= largest - 0.5]


def _right_column_name_rects(page: fitz.Page) -> list[fitz.Rect]:
    boundary = page.rect.width * 0.45
    return [
        rect for text, rect in _line_records(page) if rect.x0 >= boundary and is_name_like(text)
    ]


def _contact_rects(page: fitz.Page) -> list[fitz.Rect]:
    rectangles = []
    for text, rect in _line_records(page):
        folded = text.casefold()
        if any(marker in folded for marker in REDACTION_MARKERS):
            continue
        if any(hint in folded for hint in CONTACT_HINTS) or any(
            pattern.search(text) for _, pattern, _ in DIRECT_PATTERNS
        ):
            rectangles.append(rect)
    rectangles.extend(fitz.Rect(link["from"]) for link in page.get_links())
    return rectangles


def redact_pdf(source: Path, destination: Path) -> dict[str, int]:
    document = fitz.open(source)
    counts: dict[str, int] = {}
    for page_index, page in enumerate(document):
        text = page.get_text("text")
        candidates = [
            (category, item.group(0), replacement)
            for category, pattern, replacement in DIRECT_PATTERNS
            for item in pattern.finditer(text)
        ]
        replacements: list[tuple[fitz.Rect, str, str]] = []
        seen: set[tuple[float, float, float, float]] = set()
        for category, value, replacement in candidates:
            for rect in page.search_for(value):
                key = (rect.x0, rect.y0, rect.x1, rect.y1)
                if key not in seen:
                    seen.add(key)
                    replacements.append((rect, replacement, category))
        positioned = [
            *(("[NAME REMOVED]", "name", rect) for rect in _top_name_rects(page)),
            *(
                ("[NAME REMOVED]", "right_column_name", rect)
                for rect in _right_column_name_rects(page)
            ),
            *(("[CONTACT REMOVED]", "contact", rect) for rect in _contact_rects(page)),
        ]
        if source.stem.casefold() in FORCED_HEADER_REDACTION and page_index == 0:
            positioned.append(
                (
                    "",
                    "forced_header_name",
                    fitz.Rect(0, 0, page.rect.width, page.rect.height * 0.20),
                )
            )
        for replacement, category, rect in positioned:
            key = (rect.x0, rect.y0, rect.x1, rect.y1)
            if key not in seen:
                seen.add(key)
                replacements.append((rect, replacement, category))
        for link in page.get_links():
            page.delete_link(link)
        for rect, _, category in replacements:
            page.add_redact_annot(rect, fill=(1, 1, 1))
            counts[category] = counts.get(category, 0) + 1
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(destination, garbage=4, deflate=True)
    document.close()
    return counts


def unresolved_personal_fields(path: Path) -> dict[str, int]:
    document = fitz.open(path)
    try:
        return {
            "names": sum(
                len(_top_name_rects(page)) + len(_right_column_name_rects(page))
                for page in document
            ),
            "contacts": sum(len(_contact_rects(page)) for page in document),
            "links": sum(len(page.get_links()) for page in document),
        }
    finally:
        document.close()


def unresolved_right_column_names(path: Path) -> int:
    return unresolved_personal_fields(path)["names"]


def safe_manifest_entry(source: Path, categories: dict[str, int]) -> dict[str, object]:
    return {
        "source_id": source.stem,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "privacy_status": "PENDING_HUMAN_REVIEW",
        "redaction_counts": categories,
    }
