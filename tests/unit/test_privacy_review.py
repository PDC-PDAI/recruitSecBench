from __future__ import annotations

from recruitsecbench.privacy.review import ReviewerRole, import_review


def test_import_review_validates_human_attestation() -> None:
    review = import_review(
        {
            "review_id": "review-001",
            "derivative_id": "derived-001",
            "reviewer_id": "reviewer-001",
            "role": ReviewerRole.PRIMARY,
            "decision": "APPROVE",
            "attestation_hash": "a" * 64,
        }
    )
    assert review.reviewer_id == "reviewer-001"
