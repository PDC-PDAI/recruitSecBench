"""Select the historical defense implementations without global monkeypatches."""

from __future__ import annotations

from enum import Enum
from importlib import import_module
from typing import Any, Literal


class Defense(str, Enum):
    BASELINE = "baseline"
    BASELINE_R1 = "baseline_r1"
    FIDES = "fides"
    CAMEL = "camel"


def build_service(defense: Defense | str, role: Literal["questionnaire", "evaluation"]) -> Any:
    selected = Defense(defense)
    module = (
        f"rscb_questionnaire.services.{role}.service"
        if selected is Defense.BASELINE
        else f"rscb_questionnaire.variants.{selected.value}.{role}"
    )
    name = "QuestionnaireService" if role == "questionnaire" else "EvaluationService"
    return getattr(import_module(module), name)()


def variant_prompts(defense: Defense | str) -> dict[str, str]:
    selected = Defense(defense)
    module = (
        "rscb_questionnaire.prompts.raw_prompts"
        if selected is Defense.BASELINE
        else f"rscb_questionnaire.variants.{selected.value}.prompts"
    )
    return import_module(module).PROMPTS


DEFENSE_REVISIONS = {
    "baseline_r1": "acd083ab3c7adfad1949abf8607665afde24b7cc",
    "fides": "3aae97d23c8ec6610b83badb7956c46387672851",
    "camel": "804bece92622d256fc7211fb0d1ca01d9841f4ef",
    "baseline": "8fd93c0c95f8881359cf348f597a33a9ec676bd5",
}
