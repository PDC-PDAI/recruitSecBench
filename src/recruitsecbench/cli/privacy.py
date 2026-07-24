"""Commands for local-only handling of restricted source documents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated

import typer

from recruitsecbench.privacy.derivation import derive_minimized_profile, extract_local_text
from recruitsecbench.privacy.pdf_redaction import redact_pdf, safe_manifest_entry

privacy_app = typer.Typer(help="Local-only privacy workflow; never calls external providers.")


@privacy_app.command("anonymize")
def anonymize(
    raw_dir: Annotated[
        Path, typer.Option(help="Ignored local directory containing PDF/TXT CVs")
    ] = Path("pdfs"),
    output_dir: Annotated[Path, typer.Option(help="Ignored restricted output directory")] = Path(
        "data/derived-restricted"
    ),
) -> None:
    """Create restricted minimized profiles without printing CV text."""
    raw_dir = raw_dir.resolve()
    output_dir = output_dir.resolve()
    documents = sorted(
        path for path in raw_dir.iterdir() if path.suffix.lower() in {".pdf", ".txt"}
    )
    if not documents:
        raise typer.BadParameter("no PDF or TXT documents found")
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, str]] = []
    for document in documents:
        original = extract_local_text(document)
        profile = derive_minimized_profile(original)
        source_hash = hashlib.sha256(document.read_bytes()).hexdigest()
        target = output_dir / f"{document.stem}.json"
        target.write_text(
            json.dumps(
                {
                    "source_id": f"source-{document.stem}",
                    "source_sha256": source_hash,
                    "privacy_status": "PENDING_HUMAN_REVIEW",
                    "profile": profile,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        results.append({"source_id": f"source-{document.stem}", "output": target.name})
    typer.echo(json.dumps({"processed": len(results), "outputs": results}, sort_keys=True))


@privacy_app.command("redact-pdfs")
def redact_pdfs(
    raw_dir: Annotated[Path, typer.Option(help="Ignored local source PDF directory")] = Path(
        "pdfs"
    ),
    output_dir: Annotated[
        Path, typer.Option(help="Ignored restricted redacted PDF directory")
    ] = Path("data/redacted-restricted"),
) -> None:
    """Preserve original layout while redacting detected direct identifiers locally."""
    raw_dir = raw_dir.resolve()
    output_dir = output_dir.resolve()
    documents = sorted(raw_dir.glob("*.pdf"))
    if not documents:
        raise typer.BadParameter("no PDF documents found")
    manifest = []
    for document in documents:
        destination = output_dir / f"{document.stem}-redacted.pdf"
        categories = redact_pdf(document, destination)
        manifest.append(safe_manifest_entry(document, categories))
    (output_dir / "review-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8"
    )
    typer.echo(json.dumps({"processed": len(manifest), "status": "PENDING_HUMAN_REVIEW"}))
