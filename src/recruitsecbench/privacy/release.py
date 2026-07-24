"""Release gate: real-derived material remains controlled and review-evidenced."""

from __future__ import annotations

from recruitsecbench.privacy.analyzers import PrivacyAnalysis
from recruitsecbench.privacy.review import HumanPrivacyReview, ReviewDecision, ReviewerRole
from recruitsecbench.privacy.sources import SourceDocumentRecord


def release_allowed(
    source: SourceDocumentRecord, analysis: PrivacyAnalysis, reviews: list[HumanPrivacyReview]
) -> tuple[bool, tuple[str, ...]]:
    reasons = list(analysis.reason_codes)
    if not source.usable():
        reasons.append("SOURCE_NOT_USABLE")
    primary = [review for review in reviews if review.role is ReviewerRole.PRIMARY]
    secondary = [review for review in reviews if review.role is ReviewerRole.SECONDARY]
    if len(primary) != 1 or primary[0].decision is not ReviewDecision.APPROVE:
        reasons.append("PRIMARY_REVIEW_REQUIRED")
    uncertain = any(
        review.uncertainty or review.decision is ReviewDecision.UNCERTAIN for review in reviews
    )
    if uncertain and (len(secondary) != 1 or secondary[0].decision is not ReviewDecision.APPROVE):
        reasons.append("SECONDARY_REVIEW_REQUIRED")
    return not reasons, tuple(dict.fromkeys(reasons))
