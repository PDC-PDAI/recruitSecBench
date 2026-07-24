# Phase 0 Research: RecruitSecBench

## Decision 1: Hybrid benchmark topology

**Decision**: Run the complete controlled matrix in a custom AgentDojo suite and repeat a
small, preregistered subset against an isolated SmartRH application stack.

**Rationale**: AgentDojo supplies resettable environments, user tasks, injection tasks,
tool traces, and ground-truth checks. The application-backed layer validates that the
canonical model still corresponds to the real Prisma, tRPC, MCP, Agno, RAG, and state
contracts without making every scientific repetition depend on distributed services.

**Alternatives considered**:

- Application-only: rejected because provider, network, queue, database, and background
  task variance would dominate cost and reproducibility.
- Simulator-only: rejected because it would not detect drift from the deployed product
  contracts.
- UI E2E: rejected because the web interface is outside the feature scope and adds no
  oracle unavailable through API/MCP.

## Decision 2: Repository boundary and frozen snapshots

**Decision**: Modify only RecruitSecBench and rh-agent-agno. Treat smart-rh-platform and
agentrh-infra as read-only dependencies at the commits recorded in plan.md.

**Rationale**: The benchmark needs Agno hooks for dependency injection, sanitized tracing,
and optional controls, but it can consume Platform contracts through existing endpoints
and MCP tools. Pinning the inspected local commits avoids silent drift; the fact that a
repository is behind its remote is recorded, not repaired automatically.

**Alternatives considered**:

- Modify all repositories: rejected by user scope.
- Pull latest before planning: rejected because it invalidates the inspected contracts and
  could introduce unreviewed behavior.
- Copy Platform code into the benchmark: rejected because it creates a fork and hides
  integration drift.

## Decision 3: Scientific status of AgentDojo, CaMeL, and FIDES

**Decision**: Use three distinct evidence namespaces:

1. unmodified standard AgentDojo smoke results;
2. official CaMeL and FIDES reproduction/conformance results;
3. RecruitSecBench results using product-compatible adaptations.

**Rationale**: AgentDojo supports custom registered task suites. The official CaMeL code
targets AgentDojo but explicitly describes itself as a research artifact that may be
incomplete. Microsoft FIDES is an experimental Python feature coupled to Microsoft Agent
Framework. Using official runtimes directly in only some factorial cells would confound
defense with framework. Product-compatible adaptations retain the Agno runtime and are
named adaptations rather than faithful official implementations.

**Alternatives considered**:

- Official runtimes as C1/C2/C3: rejected because runtime changes would confound the 2x2
  comparison and combining both artifacts is not a defined official configuration.
- Adaptations only: rejected because correspondence to cited artifacts would be asserted
  without independent reproduction evidence.
- CAMEL-AI or Ethyca Fides: rejected by the clarified specification.

## Decision 4: Base policy envelope

**Decision**: Apply the same deterministic, deny-by-default ToolGateway to C0-C3. CaMeL
and FIDES are additional treatments, not substitutes for authorization.

**Rationale**: The constitution forbids delegating scope, identity, state, and permission
decisions to a model. Common enforcement also ensures that treatment effects measure how
the agent handles hostile content rather than whether basic authorization existed.

**ToolGateway checks**:

- authenticated synthetic actor and role;
- project/process/vacancy/application/candidate/questionnaire ancestry;
- canonical ID bindings and alias normalization;
- stage-specific tool allowlists;
- argument schemas and bounded values;
- valid state transitions and round tokens;
- idempotency keys and side-effect limits;
- stable ALLOW, DENY, HUMAN_REVIEW, or ERROR reason codes.

## Decision 5: Data formats and analytical storage

**Decision**: Keep UTF-8 JSONL records as canonical datasets, JSON manifests as freeze
roots, Parquet as content-addressed analytical derivatives, and DuckDB as an ephemeral
query engine.

**Rationale**: JSONL matches the existing public schemas and is reviewable line by line.
Parquet and DuckDB provide efficient aggregation without becoming authoritative inputs.
Every derived file links to upstream hashes.

**Alternatives considered**:

- PostgreSQL as canonical benchmark storage: rejected because it complicates distribution
  and byte-for-byte reproduction.
- Parquet only: rejected because it replaces the existing dataset contract.
- SQLite only: rejected because nested analytical data and columnar scans are less direct.

## Decision 6: Privacy pipeline

**Decision**: Process source documents locally from a required external directory and stop
at a restricted review queue during automated implementation.

**Rationale**: The user will make approximately 50 authorized CVs available during
implementation, but chose synthetic-only automatic experiments. Human approval cannot be
fabricated by the implementation agent. Therefore automated evidence is produced, while
release and experimental use remain blocked.

**Pipeline**:

1. reject raw paths inside the repository or its Git history;
2. require provenance, purpose, controller, authorization/legal basis, privacy/ethics
   approval status, retention, and revocation fields before extraction;
3. extract PDF, DOCX, or TXT locally; reject image-only content unless explicitly using a
   local OCR container;
4. detect direct identifiers with local NER plus email, phone, URL, username, document,
   and identifier patterns;
5. generalize indirect identifiers and rare combinations;
6. calculate longest normalized common span, semantic similarity, and equivalence classes;
7. validate PII=0, common span <=8 tokens, similarity <=0.80, and k>=5;
8. export minimized reviewer packets; require a second reviewer for uncertain cases;
9. quarantine revoked, expired, or later-rejected records and retain only permitted
   tombstones and non-identifiable aggregates.

No real source or derivative is submitted to a provider, Langfuse, or experimental runner.

## Decision 7: Synthetic corpus and coverage

**Decision**: Generate a fixed, coverage-driven public corpus with 64 benign and 192 paired
adversarial cases.

**Rationale**: The size covers eight benign task families and at least twenty attack
families while keeping the pilot feasible. Pairing three adversarial mutations with each
benign case supports controlled comparisons.

**Partition counts**:

| Partition | Benign | Adversarial |
|---|---:|---:|
| development | 16 | 48 |
| pilot | 8 | 24 |
| evaluation | 24 | 72 |
| holdout | 16 | 48 |

Lineage connected components, not individual rows, are partitioned. Evaluation and
holdout are frozen before control development.

## Decision 8: Application-backed execution

**Decision**: Create a benchmark-owned Compose topology that builds from frozen sibling
repositories and starts only API, MCP, Agno, PostgreSQL, RabbitMQ, MinIO, and Qdrant.

**Rationale**: The host has Docker/WSL but only 8 GB RAM and no detected GPU. Omitting the
web application, Terraform, and self-hosted Langfuse reduces resource pressure. Structured
local traces are authoritative; Langfuse remains optional.

**Application subset**: Twelve fixed synthetic cases — four benign and eight adversarial —
cover questionnaire generation/persistence, CV search/RAG/session behavior, candidate
evaluation, state transitions, cross-scope access, ID substitution, injection, and
duplicate effects.

## Decision 9: Model and embedding policy

**Decision**: Main model strata are OpenAI `gpt-5-mini` and CEIA `qwen3:8b`, as exposed
by the frozen Agno product configuration. Models are never silently substituted.

**Rationale**: One provider reflects the current product path and the other adds a distinct
model/runtime family already supported by the application. Exact returned model IDs,
provider settings, reasoning/thinking flags, token usage, and endpoint class are frozen in
run manifests.

The simulator uses a single frozen local multilingual embedding model for all conditions.
Application-backed RAG uses the collection-compatible embedding configured by the frozen
product snapshot and reports that difference as an integration limitation.

## Decision 10: Repetitions, statistics, and cost

**Decision**: Run three repetitions per case, condition, and model. The automatic synthetic
pilot has 768 observations and a default paid-cost ceiling of USD 25.

**Rationale**: Three repetitions satisfy the requirement to measure instability while
containing cost. Results aggregate by case, with repetitions nested under case rather than
treated as independent samples.

**Analysis**:

- proportions and cluster-bootstrap 95% confidence intervals;
- paired risk differences for each control versus C0;
- factorial CaMeL, FIDES, and interaction effects;
- exact or paired permutation tests when estimable;
- Holm correction across preregistered confirmatory comparisons;
- joint reporting of security, utility, latency, cost, and failure rates.

A preflight estimates cost. Crossing the ceiling yields `budget_blocked`; it never
partially selects favorable cases. Evaluation and holdout require `--confirm` and an
explicit cost ceiling.

## Decision 11: Failure and retry taxonomy

**Decision**: Persist every attempt with one of: completed, provider_error,
transport_error, harness_error, timeout, cancelled, budget_blocked, invalid_case, or
inconclusive.

**Rationale**: Operational failures cannot become SAFE, BLOCK, benign failure, or attack
success. Retries are linked to the original attempt and permitted only for predeclared
operational classes. The holdout permits one final campaign and preserves all retries.

## Decision 12: Shadow auditor and human labels

**Decision**: Run a fixed, tool-free auditor over a separately materialized sanitized view
for C0-C3. Human annotation packets remain blind and external to auditor input.

**Rationale**: This preserves the auditor as a residual semantic-risk evaluator. It cannot
change tools or states, and deterministic outcomes, human labels, and adjudications are
joined only during analysis.

Predictions contain decision, violation category, severity, short evidence, confidence,
model/configuration, and input-view hash. Original annotations remain immutable after
adjudication.

## Decision 13: Publication pipeline

**Decision**: Author the paper in English using Quarto, BibTeX, and a pinned container that
produces HTML and PDF from immutable result artifacts.

**Rationale**: Quarto supports executable analysis, citations, and multiple formats
without requiring a host installation. Tables and figures are generated from audit rows
and evidence records, not copied into prose.

A claim linter distinguishes objective, hypothesis, method, observed result,
interpretation, and limitation. Missing evidence or unexecuted results block result
language. The automatic terminal artifact is a preliminary pilot manuscript; evaluation
and holdout sections remain explicitly unexecuted until their campaigns exist.
