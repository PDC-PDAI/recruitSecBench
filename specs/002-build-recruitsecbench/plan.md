# Implementation Plan: RecruitSecBench Reproducible Agentic Security Benchmark

**Branch**: `002-build-recruitsecbench` | **Date**: 2026-07-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-build-recruitsecbench/spec.md`

## Summary

Build RecruitSecBench as a Python 3.12 scientific artifact with two execution layers:
a deterministic custom AgentDojo suite for the complete experiment matrix and a small
application-backed campaign against isolated SmartRH Platform, MCP, Agno, PostgreSQL,
RabbitMQ, MinIO, and Qdrant services. The benchmark owns canonical datasets, policies,
oracles, traces, manifests, analyses, and the English Quarto paper. Product aliases and
runtime behavior enter only through versioned adapters.

The future implementation may change this repository and `../rh-agent-agno`. It treats
`../smart-rh-platform` and `../agentrh-infra` as read-only, commit-pinned dependencies.
Automated completion includes deterministic validation, standard and custom smoke tests,
a three-repetition synthetic pilot, preliminary reports, and a manuscript containing
only observed claims. Evaluation and the single final holdout campaign remain explicit,
budget-gated commands.

## Technical Context

**Language/Version**: Python 3.12 for benchmark, orchestration, privacy, analysis, and
AgentDojo adapters; TypeScript/Node 20 interfaces are consumed from SmartRH Platform;
Quarto runs in a pinned container.

**Primary Dependencies**: uv, Pydantic 2, JSON Schema Draft 2020-12, Typer, AgentDojo,
Agno, FastAPI, Qdrant client, Microsoft Presidio-compatible local detectors,
sentence-transformers, Polars/Pandas, DuckDB, SciPy/statsmodels, Plotly/Altair, pytest,
Hypothesis, Ruff, mypy, and Bandit. CaMeL and Microsoft Agent Framework/FIDES are pinned
as research dependencies and kept behind adapters.

**Storage**: Canonical UTF-8 JSONL plus JSON manifests and SHA-256; derived Parquet for
analysis; DuckDB as an ephemeral query engine; restricted source documents and review
evidence outside Git; isolated PostgreSQL, MinIO, and Qdrant only for application-backed
runs.

**Testing**: pytest, pytest-asyncio, Hypothesis, JSON Schema validation, AgentDojo
`check-suites`, deterministic mock-model runs, contract tests against Agno/MCP, and a
containerized application-backed smoke suite.

**Target Platform**: Linux containers orchestrated from Windows 11 with Docker Desktop
and WSL2. Host has Python 3.12 and uv; no GPU, pnpm, Quarto, or Terraform is assumed.

**Project Type**: Python CLI/library, benchmark harness, dataset generator, experiment
runner, report generator, and scientific manuscript; no user-facing web interface.

**Performance Goals**: `doctor` and schema validation finish without paid calls; the
deterministic smoke suite completes in under 10 minutes on the inspected 8 GB host;
pilot execution is resumable, preserves every attempt, and refuses projected paid cost
above USD 25 by default.

**Constraints**: No original or real-derived CV content in Git, external provider calls,
stored prompts, traces, or public outputs. No production side effects. Platform and infra
repositories remain unmodified. Provider and harness failures are never scientific
outcomes. Evaluation and holdout are sealed until explicit authorization.

**Scale/Scope**: 50 authorized source documents analyzed into a restricted review queue;
64 public synthetic candidates, 4 projects, 8 hiring processes, 16 vacancies, 96
applications, 24 questionnaires, at least 240 questions and 480 answers; 64 benign and
192 adversarial cases; C0-C3 factorial conditions; OpenAI `gpt-5-mini` and CEIA
`qwen3:8b`; three repetitions.

## Constitution Check

*GATE: Passed before research and passed again after Phase 1 design.*

- **Claim-evidence traceability — PASS**: Research questions, hypotheses, endpoints,
  stopping rules, failure taxonomy, `evidence_id`, raw repetition retention, and article
  claim linting are defined before confirmatory runs. Pilot claims are labeled preliminary.
- **Security-utility comparison — PASS**: C0-C3 use identical frozen cases, seeds,
  tools, base policy gateway, models, and oracles. Utility, attack success, policy/scope
  violations, leakage, side effects, latency, cost, and uncertainty are reported together.
- **Deterministic enforcement — PASS**: A deny-by-default ToolGateway outside the model
  validates actor, scope, canonical ID bindings, allowlists, arguments, states,
  idempotency, and side-effect limits with stable reason codes in every condition.
- **Privacy and isolation — PASS**: Raw documents are external to the repository;
  automation is local; real derivatives remain restricted and pending review; public and
  application-backed experiments use only synthetic records; traces are minimized.
- **Human accountability — PASS**: No score or auditor output drives real hiring. Privacy
  release and gold labels require independent human action. The auditor is tool-free,
  shadow-only, and blind to deterministic outcomes and annotations.
- **Reproducibility and promotion — PASS**: Commits, dependencies, models, prompts,
  datasets, policies, environments, and runs are content-addressed. This is benchmark-only;
  production promotion remains a separate constitutional gate.

No constitutional exception is required. Real-source-derived profiles cannot satisfy the
release criteria until human review is completed; implementation must report that gate as
pending rather than weakening it.

## Research Questions and Experimental Design

- **RQ1**: Does RecruitSecBench reproduce valid attacks while retaining useful behavior
  across questionnaire and CV/evaluation flows?
- **RQ2**: What are the individual and interaction effects of the CaMeL and FIDES
  adaptations on attack success and benign utility?
- **RQ3**: What residual semantic violations can a shadow auditor detect without access
  to gold labels or deterministic decisions?
- **Primary endpoints**: benign task success and valid attack success rate.
- **Secondary endpoints**: policy and scope violations, PII/canary exposure, invalid
  transitions, side effects, latency, tokens, cost, abstention, and stability.
- **Design**: paired 2x2 factorial — C0 baseline, C1 CaMeL adaptation, C2 FIDES
  adaptation, C3 combined — for each model and seed.
- **Repetitions**: three per case/condition/model. Aggregate by `case_id`; never treat
  repetitions as independent cases.
- **Analysis**: paired risk differences, 95% cluster bootstrap by case, factorial main
  and interaction effects, exact/permutation tests where supported, and Holm correction.
- **Stopping**: fixed frozen case counts and repetitions; operational retries only for
  predeclared provider, transport, harness, timeout, or cancellation classes.

## Repository Snapshots and Integration Boundary

| Repository | Commit | Mutation policy | Role |
|---|---|---|---|
| `recruitsecbench` | `fe9cdd75cd66c4cbfddd4cb4c14b524ff4f30c34` | writable | datasets, harness, runner, reports, paper |
| `rh-agent-agno` | `8588d0aa835f3e2a590f1b1ae5ac855e733ae269` | writable | benchmark adapters, sanitized tracing, optional controls |
| `smart-rh-platform` | `bb20a77df80f9eb9db51203737c9ba6053e651ff` | read-only | Prisma, tRPC, MCP, state, persistence contracts |
| `agentrh-infra` | `38224ada162f5853563075cd93bb80918dc848d1` | read-only | deployed topology reference only |

The application-backed Compose definition lives in this repository, references sibling
build contexts, creates isolated networks/volumes, and starts only API, MCP, agent, and
required data services. It never targets production infrastructure or runs Terraform.

## Project Structure

### Documentation (this feature)

```text
specs/002-build-recruitsecbench/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── adapter-protocol.md
│   ├── cli.md
│   ├── experiment-config.schema.json
│   └── trace-event.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
src/recruitsecbench/
├── cli/
├── config/
├── privacy/
├── datasets/
├── validation/
├── policies/
├── agentdojo_suite/
├── adapters/
├── controls/
├── runner/
├── auditor/
├── analysis/
└── publication/

data/{domain,benign,adversarial,deterministic,audit}/
manifests/
protocol/
paper/
infra/
tests/{unit,property,contract,integration,e2e}/
```

Changes in `../rh-agent-agno` are isolated under a benchmark integration boundary and
feature flags. Existing production endpoints retain their default behavior.

**Structure Decision**: Keep the benchmark as an independent Python package and scientific
artifact. Integrate through canonical adapters rather than importing Platform database
models into dataset contracts. Use a deterministic simulator for the full matrix and a
small isolated application-backed validation layer to measure integration drift without
making experiments dependent on production services.

## Phase 0: Research Decisions

Research is consolidated in [research.md](research.md). All technology ambiguities are
resolved: hybrid topology, two-track CaMeL/FIDES validation, local-first privacy,
containerized application stack, canonical JSONL, cost-gated execution, three repetitions,
synthetic automatic campaigns, and English Quarto publication.

## Phase 1: Design and Contracts

- [data-model.md](data-model.md) defines entities, relationships, privacy lifecycle,
  questionnaire/application state machines, experiment records, and invariants.
- [contracts/adapter-protocol.md](contracts/adapter-protocol.md) separates canonical
  benchmark identities from Agno, MCP, and SmartRH aliases.
- [contracts/cli.md](contracts/cli.md) defines stable commands, exit behavior, safety
  gates, and artifacts.
- JSON schemas define experiment configuration and sanitized trace events.
- [quickstart.md](quickstart.md) provides the implementation validation sequence without
  executing a paid or holdout campaign implicitly.

### Post-design Constitution Re-check

All six checks remain PASS. The dual-layer architecture increases implementation size but
does not weaken any gate: simulator results and application-backed results have separate
namespaces; official-control reproductions are not pooled with adapted-control results;
real data cannot enter experimental partitions; and every externally visible claim is
evidence-gated.

## Delivery Sequence

1. Scaffold the package, CLI, locked dependencies, CI, config, structured failures, and
   artifact registry.
2. Extend the five dataset schemas and implement referential, partition, manifest, hash,
   PII, similarity, state, and canary validation.
3. Implement restricted document ingestion, automated privacy analysis, review export,
   quarantine, revocation, and tombstones.
4. Generate the frozen synthetic domain corpus and coverage-driven benign, adversarial,
   deterministic, and audit fixtures.
5. Implement ToolGateway, canonical adapters, mock model, deterministic oracles, and the
   custom AgentDojo suite; validate standard AgentDojo separately.
6. Add application-backed Compose and Agno integration hooks; repair only contract defects
   proven by tests, document them, then freeze C0.
7. Reproduce official CaMeL and FIDES smoke examples in separate namespaces; implement and
   conformance-test the Agno adaptations for C1-C3.
8. Implement resumable execution, budget estimation, three repetitions, sanitized traces,
   shadow auditor, and blinded annotation exports.
9. Run deterministic checks, standard/custom smoke, and the synthetic pilot if credentials
   are present and projected paid cost is at most USD 25.
10. Generate raw metrics, paired statistics, figures, evidence index, preliminary English
    manuscript, and reproducibility bundle.

## Complexity Tracking

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Simulator plus application-backed layer | Separates scalable controlled experiments from real integration behavior | Application-only runs are expensive and nondeterministic; simulator-only results would not validate SmartRH integration |
| Official reproduction plus Agno adaptation for each control | Preserves scientific honesty and product comparability | Official runtimes confound the factorial comparison; adaptation-only work cannot establish correspondence to cited artifacts |
| Canonical JSONL plus derived Parquet | Publication contract and efficient reproducible analysis have different access patterns | JSONL-only analysis is cumbersome; Parquet-only would replace the specified public contract |
