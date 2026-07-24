# Quickstart Validation Guide

This guide defines the runnable acceptance path for the future implementation. Commands
that do not yet exist are interface commitments from the plan, not evidence that an
experiment has already run.

## 1. Prerequisites

Required:

- Windows 11 with Docker Desktop and WSL2, or an equivalent Linux Docker host;
- Python 3.12 and uv;
- sibling repositories at the commits recorded in [plan.md](plan.md);
- at least 8 GB RAM and 20 GB free workspace/container storage;
- no service bound to the benchmark-configured isolated ports.

Optional for model-backed pilot:

- `OPENAI_API_KEY` authorized for synthetic benchmark data;
- CEIA endpoint access;
- an explicit cost ceiling.

The host does not need pnpm, Quarto, Terraform, or a GPU. Node and Quarto operations run
inside pinned containers.

## 2. Install and inspect

From the RecruitSecBench root:

```powershell
uv sync --locked
uv run rscb doctor --json
```

Expected:

- package and schema versions are reported;
- the four repository commits match the frozen plan;
- Docker is available;
- missing optional credentials are reported without exposing values;
- no model call occurs unless `--probe-models` is supplied.

A commit mismatch, unsafe storage path, or unresolved manifest dependency is a blocking
error.

## 3. Validate the existing schemas and examples

```powershell
uv run rscb data validate --report artifacts/validation/bootstrap.json
uv run pytest tests/unit tests/property tests/contract
```

Expected:

- JSON Schema Draft 2020-12 validation passes;
- canonical examples resolve all references;
- intentionally invalid fixtures fail with their stable reason codes;
- no network or paid model is used.

## 4. Generate the public synthetic corpus

```powershell
uv run rscb data synthesize --seed 20260722
uv run rscb data validate --report artifacts/validation/synthetic.json
uv run rscb freeze development --artifact-version 0.1.0
uv run rscb freeze pilot --artifact-version 0.1.0
```

Expected counts:

- 64 candidates;
- 4 projects, 8 hiring processes, 16 vacancies;
- 96 applications;
- 24 questionnaires, at least 240 questions and 480 answers;
- 64 benign and 192 adversarial cases across all partitions.

Running synthesis again with identical versions and seed must reproduce canonical bytes,
counts, and SHA-256 hashes. Lineage isolation must be zero violations.

Do not freeze evaluation or holdout until prompts, policies, models, repetitions,
statistical analysis, and failure taxonomy are preregistered.

## 5. Exercise the privacy pipeline safely

Set two paths outside the repository:

```powershell
$env:RSCB_RAW_CV_DIR = ''C:\restricted\recruitsecbench\raw''
$env:RSCB_PRIVACY_LEDGER = ''C:\restricted\recruitsecbench\ledger.jsonl''
uv run rscb privacy ingest --raw-dir $env:RSCB_RAW_CV_DIR --ledger $env:RSCB_PRIVACY_LEDGER
uv run rscb privacy analyze --source-manifest ''C:\restricted\recruitsecbench\source-manifest.json''
uv run rscb privacy review export --output ''C:\restricted\recruitsecbench\review-packets''
```

Expected:

- a path under the repository is rejected;
- no extracted text is written to Git, normal logs, prompts, traces, or public datasets;
- every source has governance metadata before extraction;
- automatic checks report PII, common-span, similarity, k, structure, and reason codes;
- passing automation ends at `PENDING_HUMAN_REVIEW`;
- no real-derived profile appears in the synthetic campaign.

The automated implementation is successful when approximately 50 source outcomes or a
protocolled shortfall are recorded. It is not a release approval.

## 6. Validate AgentDojo independently

```powershell
uv run rscb agentdojo smoke-standard
uv run rscb suite check
uv run rscb run smoke --execution-layer simulator --condition C0 --model mock
```

Expected:

- standard AgentDojo output is stored under `agentdojo_standard`;
- custom suite ground truth completes all valid smoke tasks;
- standard results are absent from RecruitSecBench aggregations;
- operational failures retain their operational status.

A full standard AgentDojo run requires an explicit `--full` and cost configuration.

## 7. Reproduce official control artifacts

```powershell
uv run rscb controls reproduce camel
uv run rscb controls reproduce fides
uv run pytest tests/contract/controls
```

Expected:

- upstream version/commit and license metadata are recorded;
- official examples produce isolated conformance reports;
- CaMeL/FIDES official results are not classified as RecruitSecBench C1-C3 results;
- Agno adaptation tests document supported and unsupported semantics.

## 8. Start the isolated SmartRH stack

```powershell
uv run rscb stack doctor
uv run rscb stack up
uv run rscb stack reset --fixture-manifest manifests/application-smoke.json
uv run pytest tests/e2e/application
```

Expected:

- only the benchmark Compose project and isolated volumes are used;
- Platform API, MCP, Agno, PostgreSQL, RabbitMQ, MinIO, and Qdrant become healthy;
- synthetic fixtures map to canonical IDs;
- the 12 registered E2E cases finish or retain explicit operational failures;
- state and side-effect snapshots match deterministic oracles.

Cleanup:

```powershell
uv run rscb stack down
```

The command must refuse shared or production-looking project names and volumes.

## 9. Cost preflight and pilot

```powershell
uv run rscb run pilot --condition all --model all --repetitions 3 --max-cost-usd 25 --dry-run
```

Review expected calls, tokens, estimated cost, missing credentials, timeouts, and the
immutable run-group ID. If acceptable:

```powershell
uv run rscb run pilot --condition all --model all --repetitions 3 --max-cost-usd 25
```

Expected:

- 768 case/condition/model/repetition observations are scheduled;
- attempts are resumable and never overwritten;
- cost is blocked before exceeding USD 25;
- provider/harness/timeouts remain separate from utility or attack outcomes;
- no evaluation or holdout record is opened.

If credentials are unavailable, retain a truthful `provider_unavailable`/blocked report
and do not generate synthetic result numbers.

## 10. Run the shadow auditor and build evidence

```powershell
uv run rscb audit run --run-group <PILOT_RUN_GROUP_ID>
uv run rscb report build --run-group <PILOT_RUN_GROUP_ID>
```

Expected:

- auditor input contains no deterministic outcomes, human labels, adjudications, PII, or
  full prompts;
- auditor predictions are stored separately;
- primary endpoints, paired comparisons, cluster-bootstrap intervals, factorial effects,
  costs, latency, and operational failures are regenerated;
- every table and figure has an `evidence_id`.

## 11. Render the English manuscript

```powershell
uv run rscb paper render --run-group <PILOT_RUN_GROUP_ID>
```

Expected:

- pinned Quarto container emits HTML and PDF;
- executed pilot results are labeled preliminary;
- missing evaluation, holdout, or human labels are stated as pending;
- quantitative claims without compatible evidence fail the build;
- no table or number requires manual editing.

## 12. Confirmatory campaigns

Evaluation requires the frozen protocol and an explicit budget:

```powershell
uv run rscb run evaluation --condition all --model all --repetitions 3 --confirm --max-cost-usd <LIMIT>
```

Holdout is a separate, one-time final campaign:

```powershell
uv run rscb run holdout --condition all --model all --repetitions 3 --confirm --max-cost-usd <LIMIT>
```

The holdout command must refuse:

- a missing or changed protocol freeze;
- a second campaign identifier;
- changed cases, prompts, policies, tools, models, or analysis;
- retries outside the predefined operational taxonomy.

After either campaign, rebuild the report and paper from the new immutable run group.
