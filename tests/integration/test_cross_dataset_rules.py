from copy import deepcopy

from recruitsecbench.datasets.cases import generate_benign_cases
from recruitsecbench.datasets.deterministic import generate_deterministic_fixtures
from recruitsecbench.datasets.domain import generate_domain
from recruitsecbench.validation.cross_rules import cross_dataset_issues


def test_complete_domain_passes_detailed_cross_rules() -> None:
    assert (
        cross_dataset_issues(
            generate_domain(), generate_benign_cases(), generate_deterministic_fixtures()
        )
        == []
    )


def test_type_scope_version_and_side_effect_codes_are_stable() -> None:
    domain = deepcopy(generate_domain())
    benign = deepcopy(generate_benign_cases())
    fixtures = deepcopy(generate_deterministic_fixtures())
    questionnaire = next(row for row in domain if row["record_type"] == "questionnaire")
    questionnaire["content"]["version"] = 3
    benign[0]["actor_id"] = "actor-unknown"
    fixtures[1]["expected_side_effect_count"] = 1
    codes = {code for code, _, _ in cross_dataset_issues(domain, benign, fixtures)}
    assert {
        "VERSION_HISTORY_INVALID",
        "ACTOR_SCOPE_INVALID",
        "DENIED_SIDE_EFFECT",
    } <= codes
