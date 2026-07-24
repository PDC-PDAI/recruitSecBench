from __future__ import annotations

from datetime import date, timedelta

from recruitsecbench.privacy.analyzers import analyze_privacy
from recruitsecbench.privacy.release import release_allowed
from recruitsecbench.privacy.review import HumanPrivacyReview, ReviewDecision, ReviewerRole
from recruitsecbench.privacy.sources import SourceDocumentRecord, SourceState


def _source() -> SourceDocumentRecord:
    return SourceDocumentRecord(
        source_id="source-001",
        relative_path="C:/restricted/source.pdf",
        content_sha256="a" * 64,
        origin="authorized",
        purpose="curation",
        controller="controller",
        responsible_person="owner",
        legal_basis="consent",
        authorization_evidence="ref",
        privacy_approved=True,
        retention_until=date.today() + timedelta(days=1),
        revocation_policy="quarantine",
        state=SourceState.AUTHORIZED,
    )


def _review(role: ReviewerRole) -> HumanPrivacyReview:
    return HumanPrivacyReview(
        review_id=f"review-{role.value.lower()}",
        derivative_id="derived-001",
        reviewer_id=f"reviewer-{role.value}",
        role=role,
        decision=ReviewDecision.APPROVE,
        attestation_hash="b" * 64,
    )


def test_release_requires_clean_analysis_and_primary_review() -> None:
    clean = analyze_privacy(
        "alpha beta", "generalized profile", quasi_identifier_tuples=[("general",)] * 5
    )
    allowed, reasons = release_allowed(_source(), clean, [])
    assert not allowed and "PRIMARY_REVIEW_REQUIRED" in reasons
    allowed, reasons = release_allowed(_source(), clean, [_review(ReviewerRole.PRIMARY)])
    assert allowed and not reasons


def test_release_blocks_revoked_or_privacy_failing_source() -> None:
    source = _source()
    source.state = SourceState.REVOKED
    failing = analyze_privacy("text", "candidate@example.com", quasi_identifier_tuples=[("x",)])
    allowed, reasons = release_allowed(source, failing, [_review(ReviewerRole.PRIMARY)])
    assert not allowed
    assert {"PII_DETECTED", "SOURCE_NOT_USABLE"} <= set(reasons)
