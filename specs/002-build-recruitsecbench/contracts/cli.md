# RecruitSecBench CLI Contract

## General behavior

Executable: `rscb`.

All commands support `--config PATH`, `--json`, and `--log-level`. Human-readable
output goes to stderr; structured results go to stdout when `--json` is used. Secrets,
raw CV text, and full prompts are never printed.

Exit codes:

| Code | Meaning |
|---:|---|
| 0 | completed successfully |
| 2 | invalid command or configuration |
| 3 | validation or policy gate failed |
| 4 | required dependency/service unavailable |
| 5 | privacy/review gate blocked |
| 6 | projected or observed budget blocked |
| 7 | operational experiment failure |
| 8 | frozen artifact or holdout violation |

## Commands

### `rscb doctor`

Checks host tools, Docker, repository commits, dependency lock, model endpoints,
credentials by presence only, application health, storage isolation, and writable artifact
paths. It performs no model call unless `--probe-models` is explicitly passed.

### `rscb privacy ingest --raw-dir PATH --ledger PATH`

Requirements:

- both paths resolve outside the repository;
- source records pass provenance/authorization prechecks;
- accepted files are PDF, DOCX, or TXT;
- extraction is local;
- no experiment dataset is produced.

Output: restricted source inventory and extraction status.

### `rscb privacy analyze --source-manifest PATH`

Runs identifier, PII, common-span, semantic-similarity, quasi-identifier, and structural
checks. Output is a restricted privacy-analysis manifest. Passing automation produces
`PENDING_HUMAN_REVIEW`, not release approval.

### `rscb privacy review export --output PATH`

Writes minimized reviewer packets outside the public dataset tree. It never auto-creates
human approvals.

### `rscb data synthesize --seed INTEGER`

Generates the fixed public domain corpus and coverage matrix. Same seed, schema versions,
and generator version must produce the same canonical bytes and hashes.

### `rscb data validate [--dataset NAME] [--report PATH]`

Validates JSON Schema, IDs, references, scopes, states, lineages, manifests, hashes,
canaries, PII, coverage, and audit separation. Emits human-readable and machine-readable
reports.

### `rscb freeze PARTITION --artifact-version SEMVER`

Valid partitions: development, pilot, evaluation, holdout. Freeze refuses dirty inputs,
missing reviews, cross-partition lineages, or incompatible dependencies. Evaluation and
holdout require protocol and analysis-plan hashes. Holdout additionally creates a sealed
access record.

### `rscb agentdojo smoke-standard`

Runs unmodified standard AgentDojo scenarios in namespace `agentdojo_standard`.
`--full` is required for anything beyond the low-cost smoke set. Results cannot be
consumed by RecruitSecBench aggregations.

### `rscb controls reproduce camel|fides`

Runs pinned official-artifact examples in namespace `official_control_reproduction`.
Outputs conformance evidence and limitations, not RecruitSecBench treatment metrics.

### `rscb stack up|down|reset|doctor`

Operates only on the benchmark-owned Compose project and isolated resources. `reset`
requires the project name to start with `rscb-` and refuses external/shared volumes.

### `rscb run smoke|pilot|evaluation|holdout`

Common options:

- `--condition C0|C1|C2|C3|all`
- `--model MODEL_ID|all`
- `--repetitions INTEGER`
- `--max-cost-usd DECIMAL`
- `--resume RUN_GROUP_ID`
- `--execution-layer simulator|application|both`
- `--confirm`

Defaults:

- smoke: one repetition, simulator, no paid call unless configured;
- pilot: three repetitions, all conditions/models, simulator plus registered E2E subset,
  maximum USD 25;
- evaluation: three repetitions and requires `--confirm --max-cost-usd`;
- holdout: three repetitions, requires sealed protocol plus explicit confirmation, and may
  create only the one preregistered final campaign.

A budget estimate happens before calls. Partial prior runs are resumed by the immutable
run key; results are never overwritten.

### `rscb audit run --run-group ID`

Materializes the sanitized auditor view, hashes it, invokes the fixed tool-free auditor,
and stores predictions separately from deterministic outcomes and human annotations.

### `rscb report build --run-group ID`

Produces validated raw metrics, aggregated metrics, uncertainty, tables, figures,
failure accounting, evidence records, and a static HTML report. Incompatible manifests
cause exit code 3.

### `rscb paper render [--run-group ID]`

Builds the English Quarto manuscript through the pinned container. If no compatible
observed evidence exists, result sections are rendered as not executed. A claim lint
failure stops the build.

### `rscb reproduce pilot`

Runs doctor, synthetic generation, validation, freeze checks, AgentDojo smoke, custom
suite smoke, pilot budget preflight, pilot when authorized, audit, report, and paper.
It never opens evaluation or holdout implicitly.

## Configuration precedence

1. command-line arguments;
2. named experiment configuration file;
3. non-secret environment variables;
4. documented defaults.

Secrets are accepted only from environment variables or an external secret provider and
are represented in manifests by provider/key identifiers, never values.
