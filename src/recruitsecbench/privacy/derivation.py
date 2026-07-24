"""Local-only extraction and minimized derivation of restricted CV sources."""

from __future__ import annotations

import re
from pathlib import Path


def extract_local_text(path: Path) -> str:
    """Extract locally. PDF support is optional rather than silently sending content away."""
    suffix = path.suffix.casefold()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError("PDF extraction requires the local pypdf dependency") from error
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    raise ValueError("only local TXT and PDF sources are supported")


def derive_minimized_profile(original: str) -> str:
    """Return allow-listed skill categories only; never return CV prose."""
    vocabulary = {
        "python",
        "java",
        "javascript",
        "typescript",
        "sql",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "linux",
        "git",
        "react",
        "angular",
        "django",
        "flask",
        "pandas",
        "spark",
        "machine",
        "learning",
        "security",
        "agile",
        "scrum",
        "english",
        "portuguese",
        "spanish",
        "excel",
        "power",
        "bi",
        "devops",
    }
    found = sorted(
        {
            token.casefold()
            for token in re.findall(r"[A-Za-z+#.]{2,}", original)
            if token.casefold() in vocabulary
        }
    )
    skills = ", ".join(found) if found else "skills pending human review"
    return f"Anonymized professional profile; generalized skills: {skills}."
