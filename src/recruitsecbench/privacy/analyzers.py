"""Offline, deterministic privacy checks for restricted derivatives."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

PII_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d[\d .()-]{7,}\d)\b"),
    "url": re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE),
    "document_id": re.compile(r"\b\d{3}[. -]?\d{3}[. -]?\d{3}[- ]?\d{2}\b"),
}
TOKEN = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


@dataclass(frozen=True)
class PrivacyAnalysis:
    pii_findings: dict[str, int]
    longest_common_span: int
    semantic_similarity: float
    k_anonymity: int
    structural_valid: bool
    reason_codes: tuple[str, ...]

    @property
    def approved_automatically(self) -> bool:
        return not self.reason_codes


def _tokens(text: str) -> list[str]:
    return [part.casefold() for part in TOKEN.findall(text)]


def longest_common_token_span(left: str, right: str) -> int:
    a, b = _tokens(left), _tokens(right)
    previous = [0] * (len(b) + 1)
    best = 0
    for item in a:
        current = [0]
        for index, candidate in enumerate(b, 1):
            value = previous[index - 1] + 1 if item == candidate else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def lexical_semantic_similarity(left: str, right: str) -> float:
    """Versioned conservative fallback: Jaccard token similarity, no provider/model call."""
    a, b = set(_tokens(left)), set(_tokens(right))
    return len(a & b) / len(a | b) if a or b else 0.0


def analyze_privacy(
    original: str,
    derivative: str,
    *,
    quasi_identifier_tuples: list[tuple[str, ...]],
    structural_valid: bool = True,
) -> PrivacyAnalysis:
    findings = {name: len(pattern.findall(derivative)) for name, pattern in PII_PATTERNS.items()}
    findings = {name: count for name, count in findings.items() if count}
    span = longest_common_token_span(original, derivative)
    similarity = lexical_semantic_similarity(original, derivative)
    count = Counter(quasi_identifier_tuples)
    candidate_key = quasi_identifier_tuples[0] if quasi_identifier_tuples else ()
    k_value = count[candidate_key] if candidate_key else 0
    reasons: list[str] = []
    if findings:
        reasons.append("PII_DETECTED")
    if span > 8:
        reasons.append("COMMON_SPAN_EXCEEDED")
    if similarity > 0.80:
        reasons.append("SEMANTIC_SIMILARITY_EXCEEDED")
    if k_value < 5:
        reasons.append("K_ANONYMITY_TOO_LOW")
    if not structural_valid:
        reasons.append("STRUCTURAL_VALIDATION_FAILED")
    return PrivacyAnalysis(findings, span, similarity, k_value, structural_valid, tuple(reasons))
