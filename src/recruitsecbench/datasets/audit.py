"""Privacy-minimized deterministic audit records for all benchmark cases."""

from __future__ import annotations

import hashlib
from typing import Any


def generate_audit_records(cases: list[dict[str, Any]], seed: int = 2026) -> list[dict[str, Any]]:
    """Create one sanitized trace per case without prompts, CV content, or gold labels."""

    traces: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        is_attack = case["case_id"].startswith("attack-")
        case_id = case["case_id"]
        traces.append(
            {
                "trace_id": f"trace-{index:03d}",
                "run_id": f"run-{index:03d}",
                "case_id": case_id,
                "partition": case["partition"],
                "condition": "C0",
                "model_id": "mock-deterministic-v1",
                "configuration_id": "config-c0-synthetic",
                "seed": seed,
                "repetition": 1,
                "execution_status": "completed",
                "tools": ["cv.search", "questionnaire.read"],
                "policy_decision": "DENY" if is_attack else "ALLOW",
                "initial_state": "EM_AVALIACAO",
                "final_state": "EM_AVALIACAO",
                "side_effect_count": 0,
                "canary_status": "not_exposed",
                "outcomes": {
                    "utility": "not_applicable" if is_attack else "success",
                    "attack": "blocked" if is_attack else "not_applicable",
                    "policy": "compliant",
                    "auditor": "pending_shadow_review",
                },
                "events": [
                    {
                        "sequence": 1,
                        "type": "case_started",
                        "content_hash": hashlib.sha256(f"{case_id}:start".encode()).hexdigest(),
                    },
                    {
                        "sequence": 2,
                        "type": "policy_decided",
                        "content_hash": hashlib.sha256(f"{case_id}:policy".encode()).hexdigest(),
                    },
                    {
                        "sequence": 3,
                        "type": "oracle_completed",
                        "content_hash": hashlib.sha256(f"{case_id}:oracle".encode()).hexdigest(),
                    },
                ],
                "sanitized": True,
                "privacy_notice": "synthetic_metadata_only",
            }
        )
    return traces
