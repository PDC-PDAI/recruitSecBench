"""Restricted PDF rendering for privacy-reviewable anonymized resumes."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer


def render_anonymized_resume(*, source_id: str, skills: list[str], destination: Path) -> None:
    """Render a deliberately generalized resume for human privacy review.

    It contains no names, contact details, employers, locations, dates, project names,
    or copied career prose. It is a restricted draft, never an automatic release.
    """
    groups = {
        "Software development": {
            "python",
            "java",
            "javascript",
            "typescript",
            "react",
            "angular",
            "django",
            "flask",
        },
        "Data and analytics": {
            "sql",
            "pandas",
            "spark",
            "machine",
            "learning",
            "bi",
            "power",
            "excel",
        },
        "Cloud and platform": {
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "linux",
            "devops",
            "git",
        },
        "Professional practices": {"agile", "scrum", "security"},
        "Languages": {"english", "portuguese", "spanish"},
    }
    styles = getSampleStyleSheet()
    body: list[Flowable] = [
        Paragraph("Anonymized Professional Profile - Restricted Review Draft", styles["Title"])
    ]
    body += [Spacer(1, 0.4 * cm), Paragraph(f"Reference: {source_id}", styles["Normal"])]
    body += [Paragraph("Status: PENDING_HUMAN_REVIEW", styles["Normal"]), Spacer(1, 0.4 * cm)]
    body.append(Paragraph("Professional summary", styles["Heading2"]))
    body.append(
        Paragraph(
            (
                "Generalized professional profile derived locally. Direct identifiers, "
                "employers, locations, dates, project names, and original prose are "
                "intentionally excluded."
            ),
            styles["BodyText"],
        )
    )
    for heading, vocabulary in groups.items():
        selected = sorted(set(skills) & vocabulary)
        if selected:
            body.append(Spacer(1, 0.25 * cm))
            body.append(Paragraph(heading, styles["Heading2"]))
            body.append(Paragraph(", ".join(selected), styles["BodyText"]))
    body += [
        Spacer(1, 0.4 * cm),
        Paragraph(
            (
                "Human reviewer must confirm the profile remains non-identifying "
                "before any controlled use."
            ),
            styles["Italic"],
        ),
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(destination), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm).build(
        body
    )

