# Architecture and development

[🇧🇷 Português](development.md) · 🇺🇸 **English** · [Home](../../README.en.md)

## Runtime and configuration

The `recruitsecbench` Python distribution contains the `rscb_questionnaire` package. Run commands from the repository root: one `pyproject.toml`
defines dependencies, commands and tests; `uv.lock` pins the reproduction environment.

The default profile and battery corpus are bundled in the distribution. The
installed CLI works outside the checkout. `.env` and SQLite use the working
directory or `QUESTIONNAIRE_HOME`. Remote prompt names use
`recruitsecbench/questionnaire/`, with a namespace for each defense.

The full pipeline selects both generator and evaluator through `--defense` or
`QUESTIONNAIRE_DEFENSE`. The API stores that choice in the scenario and uses it
for subsequent evaluations. See [defenses and the R1 battery](defenses.en.md)
for comparison protocols and the implementation map.

## Components

| Path under `rscb_questionnaire/` | Responsibility |
|---|---|
| `variants/`, `battery.py` | Historical baselines, FIDES/CaMeL and generation battery |
| `agents/` | Models and provider/role adaptation |
| `prompts/` | Local content, templates, and Langfuse resolution |
| `services/job_description/`, `services/coordinator_prompt/` | Scenario preparation and commands |
| `services/questionnaire/` | ReAct, tools, and questionnaire validation |
| `services/response/`, `services/submission/` | Synthetic cases and answer validation |
| `services/evaluation/` | `FORMULARIO` evaluation and deterministic oracle |
| `services/scenario/` | Orchestration and benchmark records |
| `services/agent_debug/`, `services/observability/` | Trajectory contract, checkpoints, and tracing |
| `api/`, `repositories/` | API and SQLite persistence |
| `schemas/` | Executable contracts |
| `sync_prompts.py`, `profiles/security.yaml` | Resources included in the installed package |

## Change the experiment

For an answer category, update `schemas/response/schema.py`, generator prompts,
the oracle when needed, and benign/adversarial tests. Threshold or canary
interpretation changes modify the protocol: document them and separate new
results from previous ones.

For providers, update `agents/model.py` and verify inheritance/overrides with
role tests. For API contracts, keep `weight` and `rationale` out of public views
and validate submissions before evaluation. SQLite migrations must preserve
existing data and evaluation idempotency.

```bash
uv run ruff check .
uv run pytest -q
uv build
```

Tests cover substitute models, adversarial answers, provenance, submissions,
exports, and API behavior. CI checks the experiment using the single root installation. Tests do not
make paid LLM calls or synchronize remote prompts.

Historical import records live in [`docs/provenance/`](../provenance/). Paths and
hashes in those JSON files describe the original import, before the move into
`src/` and `tests/questionnaire/`; they are not manifests of the current checkout.
Prompts, corpus and historical defense revisions were preserved during reorganization.
