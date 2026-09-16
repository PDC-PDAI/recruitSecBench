# Baselines, FIDES, CaMeL and the R1 battery

[🇧🇷 Português](defenses.md) · 🇺🇸 **English** · [Home](../../README.en.md)

## Experimental variants

FIDES and CaMeL implement defense mechanisms for comparing how questionnaire
generation and answer evaluation handle adversarial content. Each variant
selects a generator and an evaluator under the same scenario contract.

| `--defense` | Role in the experiment | Generator and evaluator |
|---|---|---|
| `baseline` | Default full-pipeline baseline | Standard generation and evaluation services |
| `baseline_r1` | Reference for the R1 battery | R1 generation and evaluation services |
| `fides` | Defense with information-flow labels | Opaque references, integrity/confidentiality labels, reference monitor and quarantined LLM |
| `camel` | Defense with control/data separation | Quarantined processing and output provenance policies |

These are experimental project implementations. Local tests do not establish
robustness against real models or full equivalence to the reference implementations
of the FIDES/CaMeL papers.

## Development map

Paths below are relative to `rscb_questionnaire/`:

| Variant | Generator | Evaluator | Policies and mechanisms |
|---|---|---|---|
| Current baseline | [`services/questionnaire/service.py`](../../src/rscb_questionnaire/services/questionnaire/service.py) | [`services/evaluation/service.py`](../../src/rscb_questionnaire/services/evaluation/service.py) | Common validation and oracle |
| Baseline R1 | [`variants/baseline_r1/questionnaire.py`](../../src/rscb_questionnaire/variants/baseline_r1/questionnaire.py) | [`variants/baseline_r1/evaluation.py`](../../src/rscb_questionnaire/variants/baseline_r1/evaluation.py) | R1 implementation |
| FIDES | [`variants/fides/questionnaire.py`](../../src/rscb_questionnaire/variants/fides/questionnaire.py) | [`variants/fides/evaluation.py`](../../src/rscb_questionnaire/variants/fides/evaluation.py) | [`variants/fides/security/fides.py`](../../src/rscb_questionnaire/variants/fides/security/fides.py) |
| CaMeL | [`variants/camel/questionnaire.py`](../../src/rscb_questionnaire/variants/camel/questionnaire.py) | [`variants/camel/evaluation.py`](../../src/rscb_questionnaire/variants/camel/evaluation.py) | [`variants/camel/security/`](../../src/rscb_questionnaire/variants/camel/security/) |

Each variant retains its local prompts. Job/command preparation, answer generation,
schemas, oracle, persistence and provider integration use the shared runtime.
Selection instantiates both services without branch switching or global class
replacement. FIDES/CaMeL tests cover the mechanisms and their use by both services.

## Full pipeline including evaluation

From the repository root, after configuring `.env`:

```bash
uv run rscb-questionnaire run --defense fides \
  --brief "Backend Python and FastAPI role" \
  --output outputs/fides/run-001/scenario.json \
  --jsonl outputs/fides/run-001/benchmark.jsonl \
  --agent-debug-jsonl outputs/fides/run-001/agent-debug.jsonl \
  --trajectories-dir outputs/fides/run-001/trajectories
```

Replace `fides` with `camel`, `baseline_r1` or `baseline`, using a separate output
directory. The default profile generates commands, questionnaires, answers and
evaluations. Refusal during generation prevents later stages for that case.
`--defense` overrides `QUESTIONNAIRE_DEFENSE`, which defaults to `baseline`.
Scenarios persist `defense`; benchmark records include the variant and source commit.

In the API, send `"defense": "fides"` when creating a scenario. Manual evaluations
use the persisted scenario variant, including after a server restart with different
settings. Older scenarios without this field are interpreted as `baseline`.

With Langfuse, sync common prompts and then variant prompts:

```bash
uv run rscb-questionnaire sync-prompts --defense baseline
uv run rscb-questionnaire sync-prompts --defense fides
uv run rscb-questionnaire sync-prompts --defense camel
```

Variant services use `recruitsecbench/questionnaire/<variant>/`; shared services
continue using `recruitsecbench/questionnaire/`. Local prompts work without Langfuse.
Archive the resolved prompt content and remote versions, when used, for reproduction.

## R1 generation battery

[`rscb-questionnaire-battery`](../../src/rscb_questionnaire/battery.py) runs the generation
campaign. The [YAML corpus](../../src/rscb_questionnaire/profiles/questionnaire_battery.yaml)
contains **5 jobs × (15 themes × 5 levels + 1 control) = 380 generations per repetition**:
375 attacks and 5 controls. The YAML is also bundled in the installed package.

This battery **does not generate answers, invoke the evaluator or classify results**.
`status` records the generator's operational outcome, not a subsequent security
classification. The manifest retains `evaluation_enabled=false` and
`classification_enabled=false`.

```bash
# Validate the corpus and prepare manifest/SQLite without LLM calls
uv run rscb-questionnaire-battery --defense baseline_r1 --dry-run
uv run rscb-questionnaire-battery --defense fides --dry-run
uv run rscb-questionnaire-battery --defense camel --dry-run

# Execute at most one pending item using the configured model
uv run rscb-questionnaire-battery --defense fides --limit 1

# Resume the campaign; without --limit, execute all pending items
uv run rscb-questionnaire-battery --defense fides --concurrency 3
```

This CLI defaults to `baseline_r1`, independently of `QUESTIONNAIRE_DEFENSE`, to
identify the battery baseline. Default outputs go to
`outputs/questionnaire-battery-<variant>/`. `--output-dir`, `--config` and
`--repetitions` support separate campaigns. Each directory contains a manifest,
`generations.jsonl`, individual JSON files, `questionnaire_battery.sqlite3`, a summary
and a data dictionary. The historical format retains questionnaires, status,
trajectory/trace IDs and duration; it does not contain the full AgentDebug export.

Resume checks defense, source revision, provider/model, corpus and repetitions
before reusing a directory. Incompatible configuration requires another directory.
All recorded items, including `runtime_error`, count as completed when resuming.
Use a separate campaign to repeat those cases.
Also archive the current commit, lockfile, full provider configuration and prompts;
the manifest does not capture every external runtime parameter.

## Reproducible comparisons

Pin the RecruitSecBench commit, lockfile, corpus, resolved prompts and provider
settings for every campaign. Variants use a shared runtime; changing provider
behavior, retry settings or prompts requires recording a new configuration.

Compare `baseline_r1`, FIDES and CaMeL using the same corpus, model, parameters and
repetition count. The full pipeline generates fresh commands and answers with LLMs
and does not automatically constitute a paired comparison. Keep generation and
evaluation protocols separate, report coverage/refusals/errors and consult the
[methodology](methodology.en.md) to interpret the oracle. The repository provides code and configuration. Reanalyzing a completed campaign
requires its saved artifacts; a fresh LLM run can produce different outputs.
