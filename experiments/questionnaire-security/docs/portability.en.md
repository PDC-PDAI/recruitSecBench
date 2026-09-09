# Portability and development

[🇧🇷 Português](portability.md) · 🇺🇸 **English** · [Home](../README.en.md)

## Project boundary

This is an independent Python distribution, `recruitsecbench-questionnaire`,
with package `rscb_questionnaire` and command `rscb-questionnaire`. Its own
`pyproject.toml` and `uv.lock` retain the source dependencies. The RecruitSecBench
root retains package `recruitsecbench`, CLI `rscb`, and the previous environment.

There are no `src` imports, symlinks, Git dependencies, or paths to Scenario
Emulator. The default profile is bundled; the installed CLI works outside the
checkout. `.env` and SQLite use the runtime directory or `QUESTIONNAIRE_HOME`.

## Components

| Path under `rscb_questionnaire/` | Responsibility |
|---|---|
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

## Source adaptations

- Python namespace `src` → `rscb_questionnaire`, including dynamic import strings.
- CLI defaults to security; fault campaign commands are not ported.
- Remote prompts use `recruitsecbench/questionnaire/`; experimental content is preserved.
- Provenance and service names identify the RecruitSecBench experiment.
- Configuration/database are isolated from the parent project; prompt sync is bundled in the wheel.
- Security pipeline tests are ported; the other profile fixture only validates the boundary.

The fault runner, 100/220/1,100-case campaigns, and v2 control scripts remain in
Scenario Emulator. Fault types and AgentDebug exporters are retained because
security trajectories also use them. Previous CV code and contracts were not rewritten.

[`PORTABILITY.json`](../PORTABILITY.json) records the source commit and SHA-256
hashes of ported source and destination files. Treat it as the initial port's
reference, not an automatic synchronization mechanism for subsequent development.

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
exports, and API behavior. CI runs this project in its own job. Tests do not
make paid LLM calls or synchronize remote prompts.
