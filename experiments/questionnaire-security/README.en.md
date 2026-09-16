# Questionnaire security

[🇧🇷 Português](README.md) · 🇺🇸 **English** · [RecruitSecBench](../../README.en.md)

Execution guide for the questionnaire security experiment: job and questionnaire
generation, adversarial commands, synthetic answers and `FORMULARIO` evaluation.
See the [experiment overview and paper figures](../../README.en.md#experiment-overview).

## Baseline, FIDES and CaMeL

Variants include **both generator and evaluator**. Use `run --defense fides` or
`run --defense camel`; `baseline` is the default for the full pipeline and
`baseline_r1` is the reference for the R1 battery.

The 380-case-per-repetition battery is also included:
`uv run rscb-questionnaire-battery --defense fides --dry-run`.
It tests generation only; `run` executes the pipeline including evaluation.
See [variants, implementations and commands](docs/defenses.en.md).

## Installation and configuration

Run this guide's commands from `experiments/questionnaire-security/`.

```bash
uv sync --locked
cp .env.example .env
uv run rscb-questionnaire --help
uv run rscb-questionnaire validate-profile configs/fronts/security.yaml
```

Edit `.env` to select a provider:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5-mini
LANGFUSE_TRACING_ENABLED=false
```

Supported providers also include `openai_responses`, `openai_like`, `ollama`,
and `ceia`; see [.env.example](.env.example). Compare model roles with
`RESPONSE_GENERATOR_LLM_PROVIDER`/`RESPONSE_GENERATOR_MODEL` and
`EVALUATOR_LLM_PROVIDER`/`EVALUATOR_MODEL`. Missing overrides inherit global settings.

The runtime reads `.env` from the working directory, without searching the parent
project. `QUESTIONNAIRE_HOME` selects another directory for `.env` and the default
database. Explicit relative YAML paths and `API_DATABASE_PATH` remain relative
to the working directory. The default database is `data/questionnaire-security.db`.

## Run

A smoke run with one benign answer case, using an LLM:

```bash
uv run rscb-questionnaire run \
  --brief "Vaga sênior de backend Python, FastAPI e PostgreSQL" \
  --benign 1 --malicious 0 \
  --benign-responses 1 --malicious-responses 0
```

Default adversarial experiment:

```bash
uv run rscb-questionnaire run \
  --profile configs/fronts/security.yaml \
  --brief "Vaga sênior de backend Python, FastAPI e PostgreSQL"
```

| Default setting | Count |
|---|---:|
| Benign commands | 1 |
| Malicious commands | 3 |
| Benign answer cases per generated questionnaire | 1 |
| Malicious answer cases per generated questionnaire | 2 |

An answer case is a set of answers to the questionnaire, not one question.
The evaluator runs for each generated case. Refused or failed questionnaires do
not proceed to answer generation/evaluation. `--brief-file briefing.txt` replaces
`--brief`. Explicit flags override YAML. For generation only, use
`--benign-responses 0 --malicious-responses 0 --no-questionnaire-evaluator`.

## Preserve a run

Default paths are reused. Select fresh paths to preserve each run and archive
the profile, brief, commit, lockfile, and model configuration with it:

```bash
uv run rscb-questionnaire run \
  --brief-file briefing.txt \
  --output outputs/run-001/scenario.json \
  --jsonl outputs/run-001/benchmark.jsonl \
  --agent-debug-jsonl outputs/run-001/agent-debug.jsonl \
  --trajectories-dir outputs/run-001/trajectories
```

| Artifact | Contents |
|---|---|
| `scenario.json` | Job, commands, questionnaires, answer cases, evaluations, and benchmark records |
| `benchmark.jsonl` | One `BenchmarkRecord` per generation, answer batch, or evaluation trajectory |
| `agent-debug.jsonl` | AgentDebug trajectories; retained interchange contract |
| `trajectories/` | The same trajectories in individual files |

Executable schemas live in `rscb_questionnaire/schemas/`. The CLI can exit zero
with benchmark failures; inspect records and oracles. Do not aggregate all
trajectory types into one success rate.

## API and observability

```bash
uv run rscb-questionnaire serve --host 127.0.0.1 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`. The [API guide](docs/api.en.md) covers
public questionnaires, submissions, idempotent evaluation, and export.

Langfuse is optional. Use a dedicated project, configure its three `LANGFUSE_*`
credentials, and set `LANGFUSE_TRACING_ENABLED=true`. Prompt names use
`recruitsecbench/questionnaire/`, with a namespace for each defense.

```bash
uv run rscb-questionnaire sync-prompts
uv run rscb-questionnaire export-trace --trace-id TRACE_ID --output outputs/trace.json
```

`LANGFUSE_SYNC_LABEL` selects the synchronization target; `LANGFUSE_PROMPT_LABEL`
selects the runtime label. Set both to `dev` for development; `latest` is rejected.
Local prompt content remains available without Langfuse.

## Develop and verify

```bash
uv run ruff check .
uv run pytest -q
uv build
```

| Guide | Português | English |
|---|---|---|
| FIDES, CaMeL and R1 battery | [Defesas](docs/defenses.md) | [Defenses](docs/defenses.en.md) |
| Method, oracles, and reproduction | [Método](docs/methodology.md) | [Methodology](docs/methodology.en.md) |
| Architecture and development | [Desenvolvimento](docs/development.md) | [Development](docs/development.en.md) |
| API and submissions | [API](docs/api.md) | [API](docs/api.en.md) |

Tests use substitute models and disable tracing. They verify implementation;
they are not empirical robustness results against real models.
