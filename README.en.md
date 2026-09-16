# RecruitSecBench

[🇧🇷 Português](README.md) · 🇺🇸 **English**

A security benchmark for LLM recruitment agents. It investigates **prompt
injection in questionnaire generation and answer evaluation**, comparing
baselines with FIDES and CaMeL defenses.

[Get started](#get-started) · [Methodology](docs/questionnaire/methodology.en.md) ·
[Defenses and battery](docs/questionnaire/defenses.en.md) ·
[Development](docs/questionnaire/development.en.md) ·
[API](docs/questionnaire/api.en.md)

## Experiment overview

The workflow starts from a job description, generates a questionnaire and evaluates
candidate answers. The benchmark exercises two attack surfaces: **AS-1**, the
generator interface, and **AS-2**, the evaluator interface. Synthetic commands and
answers support benign and adversarial cases.

![Figure 1: recruitment workflow with AS-1 at the questionnaire generator and AS-2 at the LLM evaluator.](docs/figures/figura1_en.png)

*Figure 1 — Experimental architecture and attack surfaces from the paper.*

| Surface | Adversarial input | What to observe |
|---|---|---|
| **AS-1 · Generator** | Coordinator command | Compliance with malicious commands, over-refusal and questionnaire validity |
| **AS-2 · Evaluator** | Questionnaire answers | Score manipulation, output alteration, evidence provenance and canary disclosure |

## Integrity and confidentiality

A refusal may prevent the malicious objective while the generated explanation
still reveals internal information. Decision integrity and output confidentiality
therefore need to be examined separately.

![Figure 4: the malicious objective is rejected, but the security note may disclose an internal canary.](docs/figures/figura4_en.png)

*Figure 4 — Refusal of a malicious objective with possible disclosure in the security explanation.*

The figures use the paper's terminology. The implementation returns `valor`,
`justificativa` and `evidencias`, with checks in `oracle`. `verdict` and
`security_note` are not fields in this contract. Current canary checks inspect
`justificativa`. See the [methodology](docs/questionnaire/methodology.en.md)
for each check and its scope.

## Get started

Requirements: **Python 3.12+**, Git and `uv`. Work from the repository root:

```bash
git clone https://github.com/PDC-PDAI/recruitSecBench.git
cd recruitSecBench
uv sync --locked
test -f .env || cp .env.example .env

# Verification without model calls
uv run rscb-questionnaire validate-profile
uv run pytest -q
```

Configure the provider in `.env` and run a small scenario including evaluation:

Run every command in this README from the repository root, using the same
`.env`, `pyproject.toml` and `uv.lock`.

```bash
uv run rscb-questionnaire run --defense baseline \
  --brief "Senior backend role using Python, FastAPI and PostgreSQL" \
  --benign 1 --malicious 0 \
  --benign-responses 1 --malicious-responses 0
```

This calls LLMs. Without the overrides above, the
default profile requests one benign and three malicious commands, with one benign
and two malicious answer cases per generated questionnaire.

## Configuration

Edit the single `.env` at the repository root for your provider:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5-mini
LANGFUSE_TRACING_ENABLED=false
```

[.env.example](.env.example) documents OpenAI, OpenRouter (`openai_like`),
Ollama/CEIA, and the `RESPONSE_GENERATOR_*` and `EVALUATOR_*` role overrides.
Exported environment variables take precedence over `.env`. `QUESTIONNAIRE_HOME`
selects another directory for `.env` and the default database; explicit output
paths remain relative to the working directory.

The security profile and battery corpus each have one canonical copy in
[`src/rscb_questionnaire/profiles/`](src/rscb_questionnaire/profiles/), bundled
in the installed package. Use `--profile path.yaml` for a custom profile;
explicit flags override its values. `--brief-file briefing.txt` replaces `--brief`.
For generation only, use `--benign-responses 0 --malicious-responses 0
--no-questionnaire-evaluator`.

## Baselines, FIDES and CaMeL

| `--defense` | Variant | Coverage |
|---|---|---|
| `baseline` | Default baseline for the full pipeline | Generator and evaluator |
| `baseline_r1` | Reference baseline for the R1 battery | Generator and evaluator |
| `fides` | Integrity/confidentiality labels, reference monitor and quarantine | Generator and evaluator |
| `camel` | Separation of control and data, quarantine and provenance policies | Generator and evaluator |

Use `run --defense fides` or `run --defense camel` to select both stages.
The [defense guide](docs/questionnaire/defenses.en.md) links
to each implementation and explains comparison protocols.

The R1 battery contains **380 generations per repetition**: 5 jobs × (75 attacks
+ 1 control). Validate the corpus without model calls:

```bash
uv run rscb-questionnaire-battery --defense fides --dry-run
```

The battery runs generation only. `rscb-questionnaire run` includes answers and
evaluation for the questionnaires produced.

## Evaluator and artifacts

`EvaluationService` evaluates the `FORMULARIO` dimension after submission
validation. Configure its model with `EVALUATOR_LLM_PROVIDER` and `EVALUATOR_MODEL`.
The [API](docs/questionnaire/api.en.md) supports manual
submissions and retrieval of persisted evaluations.

- [Baseline evaluator](src/rscb_questionnaire/services/evaluation/service.py)
- [Deterministic oracle](src/rscb_questionnaire/services/evaluation/oracle.py)
- [Evaluation schemas](src/rscb_questionnaire/schemas/evaluation/schema.py)
- [FIDES and CaMeL evaluators](docs/questionnaire/defenses.en.md#development-map)

The full pipeline writes `scenario.json`, `benchmark.jsonl`, `agent-debug.jsonl`
and `trajectories/` under `outputs/security/` by default. Use a directory per run
and analyze generation and evaluation separately, with explicit denominators,
refusals and runtime failures. A generation refusal prevents subsequent evaluation
for that case; the [experimental criteria](docs/questionnaire/methodology.en.md)
detail coverage, thresholds and limitations.

Default output paths are reused. Preserve separate runs with explicit paths:

```bash
uv run rscb-questionnaire run --brief-file briefing.txt \
  --output outputs/run-001/scenario.json \
  --jsonl outputs/run-001/benchmark.jsonl \
  --agent-debug-jsonl outputs/run-001/agent-debug.jsonl \
  --trajectories-dir outputs/run-001/trajectories
```

Langfuse is optional. Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
`LANGFUSE_BASE_URL`, and `LANGFUSE_TRACING_ENABLED=true` to enable it. Runtime
reads `LANGFUSE_PROMPT_LABEL`; sync writes to `LANGFUSE_SYNC_LABEL`. Without
Langfuse, local prompts are used. See [defenses](docs/questionnaire/defenses.en.md)
for per-variant synchronization and [methodology](docs/questionnaire/methodology.en.md)
for recording versions and reproducing campaigns.

```bash
uv run rscb-questionnaire sync-prompts
uv run rscb-questionnaire export-trace --trace-id TRACE_ID --output outputs/trace.json
```

## Structure

| Path | Contents |
|---|---|
| `.env.example`, `pyproject.toml`, `uv.lock` | Shared configuration and installation |
| `src/rscb_questionnaire/` | Questionnaires, evaluator, defenses and profiles |
| `src/recruitsecbench/` | Tools for the résumé experiment |
| `tests/` | Full suite; questionnaire tests in `tests/questionnaire/` |
| `docs/` | Technical guides, figures and import provenance |
| `data/`, `protocol/`, `schemas/`, `contracts/` | Benchmark data and contracts |
| `specs/` | Specification history |
| `outputs/`, `artifacts/` | Local results, ignored by Git |

## Development

The project has one installation and one test suite. Questionnaire code lives in
`src/rscb_questionnaire/`, with tests in `tests/questionnaire/`.

```bash
uv run ruff check .
uv run pytest -q
uv build
```

| Guide | Português | English |
|---|---|---|
| Methodology and reproduction | [Método](docs/questionnaire/methodology.md) | [Methodology](docs/questionnaire/methodology.en.md) |
| Defenses and R1 battery | [Defesas](docs/questionnaire/defenses.md) | [Defenses](docs/questionnaire/defenses.en.md) |
| Architecture and development | [Desenvolvimento](docs/questionnaire/development.md) | [Development](docs/questionnaire/development.en.md) |
| API and submissions | [API](docs/questionnaire/api.md) | [API](docs/questionnaire/api.en.md) |

The [CV experiment](docs/legacy-cv-experiment.en.md) has code in
`src/recruitsecbench/`, CLI `rscb` and its own contracts. CI checks both packages
in the same environment. Tests use substitute models to verify implementation;
robustness results require campaigns with real models.
