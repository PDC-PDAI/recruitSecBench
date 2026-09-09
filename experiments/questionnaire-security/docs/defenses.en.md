# FIDES, CaMeL and the historical battery

[🇧🇷 Português](defenses.md) · 🇺🇸 **English** · [Home](../README.en.md)

## Why they belong here

FIDES and CaMeL are this project's defense variants for comparing how questionnaire
generation and answer evaluation handle adversarial content. The initial port
included only the active working branch; these implementations lived on separate
Scenario Emulator branches.

| `--defense` | Scenario Emulator origin | Generator and evaluator |
|---|---|---|
| `baseline` | `8fd93c0` — initial port | Implementation current when the repositories were separated |
| `baseline_r1` | `bateria-testes-r1` · `acd083a` | Historical battery baseline, retained as its own variant |
| `fides` | `feat/fides` · `3aae97d` | Opaque references, integrity/confidentiality labels, reference monitor and quarantined LLM |
| `camel` | `feat/camel` · `804bece` | Separation of control and data, quarantined processing and output provenance policies |

These are experimental project implementations. Local tests do not establish
robustness against real models or full equivalence to the reference implementations
of the FIDES/CaMeL papers.

## Development map

Paths below are relative to `rscb_questionnaire/`:

| Variant | Generator | Evaluator | Policies and mechanisms |
|---|---|---|---|
| Current baseline | [`services/questionnaire/service.py`](../rscb_questionnaire/services/questionnaire/service.py) | [`services/evaluation/service.py`](../rscb_questionnaire/services/evaluation/service.py) | Common validation and oracle |
| Baseline R1 | [`variants/baseline_r1/questionnaire.py`](../rscb_questionnaire/variants/baseline_r1/questionnaire.py) | [`variants/baseline_r1/evaluation.py`](../rscb_questionnaire/variants/baseline_r1/evaluation.py) | Historical implementation |
| FIDES | [`variants/fides/questionnaire.py`](../rscb_questionnaire/variants/fides/questionnaire.py) | [`variants/fides/evaluation.py`](../rscb_questionnaire/variants/fides/evaluation.py) | [`variants/fides/security/fides.py`](../rscb_questionnaire/variants/fides/security/fides.py) |
| CaMeL | [`variants/camel/questionnaire.py`](../rscb_questionnaire/variants/camel/questionnaire.py) | [`variants/camel/evaluation.py`](../rscb_questionnaire/variants/camel/evaluation.py) | [`variants/camel/security/`](../rscb_questionnaire/variants/camel/security/) |

Each variant retains its local prompts. Job/command preparation, answer generation,
schemas, oracle, persistence and provider integration use the shared runtime.
Selection instantiates both services without branch switching or global class
replacement. Original FIDES/CaMeL tests accompany the port.

## Full pipeline including evaluation

From `experiments/questionnaire-security/`, after configuring `.env`:

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

## Original generation battery

[`rscb-questionnaire-battery`](../rscb_questionnaire/battery.py) ports
`scripts/run_questionnaire_battery.py`. The [YAML corpus](../configs/questionnaire_battery.yaml)
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

## Fidelity and comparisons

[`DEFENSE_PORTABILITY.json`](../DEFENSE_PORTABILITY.json) records source/destination
commits and hashes for this extension. [`PORTABILITY.json`](../PORTABILITY.json)
remains the initial port snapshot. Adaptations include imports, prompt namespaces,
service selection and provenance. The shared runtime includes later retry,
OpenRouter and observability improvements, so this is not a byte-for-byte checkout
of each historical branch.

Compare `baseline_r1`, FIDES and CaMeL using the same corpus, model, parameters and
repetition count. The full pipeline generates fresh commands and answers with LLMs
and does not automatically constitute a paired comparison. Keep generation and
evaluation protocols separate, report coverage/refusals/errors and consult the
[methodology](methodology.en.md) to interpret the oracle. No historical results,
credentials or paid runs were transferred or produced by this port.
