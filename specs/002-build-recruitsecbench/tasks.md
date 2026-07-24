# Tasks: RecruitSecBench Reproducible Agentic Security Benchmark

**Input**: Design documents from `specs/002-build-recruitsecbench/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `.specify/memory/constitution.md`

**Testing rule**: Every task that changes schemas, privacy controls, policies, deterministic oracles, scope enforcement, traces, metrics, or side effects includes its required automated tests. Test work is intentionally bundled with the corresponding vertical slice so tasks remain substantial and reviewable.

## Phase 1: Setup (shared infrastructure)

**Purpose**: Establish the reproducible Python benchmark package and its developer workflow.

- [X] T001 Bootstrap the Python 3.12/uv package, locked dependency set, package layout, and test directories in `pyproject.toml`, `uv.lock`, `src/recruitsecbench/`, and `tests/`
- [X] T002 [P] Implement the Typer command shell, typed configuration loading, environment-safe defaults, and structured failure model in `src/recruitsecbench/cli/`, `src/recruitsecbench/config/`, and `tests/unit/test_cli_config.py`
- [X] T003 [P] Configure reproducibility and quality automation (Ruff, mypy, Bandit, pytest, CI, and pinned Quarto container) in `pyproject.toml`, `.github/workflows/ci.yml`, and `infra/quarto/Dockerfile`

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Build the shared contracts and safety gates required by every user story.

- [X] T004 Implement canonical Pydantic entities, canonical ID/alias rules, dataset envelopes, and Draft 2020-12 schema validation in `src/recruitsecbench/datasets/models.py`, `src/recruitsecbench/validation/schema.py`, and `tests/unit/test_canonical_models.py`
- [X] T005 [P] Implement content-addressed manifests, SHA-256 provenance, artifact registry, compatibility checks, and atomic artifact writes in `src/recruitsecbench/config/manifests.py`, `src/recruitsecbench/validation/provenance.py`, and `tests/unit/test_manifests.py`
- [X] T006 [P] Implement the shared privacy-safe structured trace/event model, stable reason codes, operational-failure taxonomy, and trace-schema validation in `src/recruitsecbench/privacy/traces.py`, `src/recruitsecbench/validation/failures.py`, `contracts/trace-event.schema.json`, and `tests/unit/test_trace_sanitization.py`
- [X] T007 [P] Implement benchmark protocol definitions for partitions, conditions C0–C3, model/config identities, seeds, evidence IDs, and explicit evaluation/holdout authorization gates in `protocol/experiment.yaml`, `src/recruitsecbench/config/protocol.py`, and `tests/unit/test_protocol_gates.py`
- [X] T008 Integrate `doctor` and `validate` CLI commands that run schema, manifest, privacy-status, provenance, and compatibility gates without provider calls in `src/recruitsecbench/cli/main.py`, `src/recruitsecbench/validation/service.py`, and `tests/integration/test_doctor_validate.py`

**Checkpoint**: The package can reject unsafe or incompatible artifacts before any story-specific run begins.

---

## Phase 3: User Story 1 — Governar e derivar perfis com segurança (P1) 🎯 MVP

**Goal**: Admit only authorized, privacy-reviewed derived profiles while keeping originals and sensitive derivatives outside the public benchmark.

**Independent Test**: Process a controlled authorized fixture through ingestion and release; verify approved output only for a clean, reviewed derivative and deterministic quarantine/revocation for every unsafe state.

- [X] T009 [US1] Implement the restricted-source registry and lifecycle (authorization, purpose, retention, revocation, tombstones, and no-Git safeguards) in `src/recruitsecbench/privacy/sources.py`, `src/recruitsecbench/privacy/lifecycle.py`, and `tests/unit/test_source_lifecycle.py`
- [X] T010 [US1] Implement local-only derivation and automated privacy analysis covering direct identifiers, quasi-identifiers, text overlap ≤8 tokens, semantic similarity ≤0.80, and k-anonymity ≥5 in `src/recruitsecbench/privacy/derivation.py`, `src/recruitsecbench/privacy/analyzers.py`, and `tests/property/test_privacy_analysis.py`
- [X] T011 [US1] Implement human-review export/import, quarantine, release gating, and repository/trace leak scans in `src/recruitsecbench/privacy/review.py`, `src/recruitsecbench/privacy/release.py`, `src/recruitsecbench/cli/privacy.py`, and `tests/integration/test_privacy_release_gate.py`

**Checkpoint**: A released profile has complete review evidence; a residual-risk or revoked source cannot enter a dataset.

---

## Phase 4: User Story 2 — Produzir os cinco datasets relacionados (P2)

**Goal**: Generate privacy-safe synthetic `domain`, `benign`, `adversarial`, `deterministic`, and `audit` datasets linked through canonical IDs and stateful relationships.

**Independent Test**: Generate a complete synthetic hiring lineage and validate all links, scope/state transitions, questionnaire oracles, and deterministic rejection of malformed fixtures.

- [X] T012 [US2] Implement the deterministic synthetic domain corpus generator for projects, processes, vacancies, candidates, documents, applications, questionnaires, questions, responses, and evaluations in `src/recruitsecbench/datasets/domain.py`, `data/domain/`, and `tests/integration/test_domain_corpus.py`
- [X] T013 [US2] Implement coverage-driven benign and adversarial case generators, including benign counterparts, required attack families, threat preconditions, prohibited outcomes, and oracle declarations in `src/recruitsecbench/datasets/cases.py`, `data/benign/`, `data/adversarial/`, and `tests/property/test_case_coverage.py`
- [X] T014 [US2] Implement deterministic tool fixtures, synthetic canaries, audit records, and questionnaire-specific structure/coverage/relevance/privacy/scope/manipulation oracles in `src/recruitsecbench/datasets/deterministic.py`, `src/recruitsecbench/datasets/audit.py`, `src/recruitsecbench/validation/oracles.py`, and `tests/unit/test_questionnaire_oracles.py`
- [X] T015 [US2] Implement cross-dataset referential, type, alias, actor-scope, state-sequence, and version-history validation with deterministic rejection codes in `src/recruitsecbench/validation/datasets.py`, `src/recruitsecbench/cli/datasets.py`, and `tests/integration/test_five_dataset_validation.py`

**Checkpoint**: All five datasets can be generated and validated as a complete synthetic scenario without product dependencies.

---

## Phase 5: User Story 3 — Congelar artefatos sem vazamento experimental (P3)

**Goal**: Freeze lineage-preserving partitions and all experiment inputs so later changes cannot silently contaminate comparisons.

**Independent Test**: Reproduce an unchanged freeze byte-for-byte; mutate an input and verify a new version is required and incompatible results cannot aggregate.

- [ ] T016 [US3] Implement lineage-aware development/pilot/evaluation/holdout partitioning, connected-component isolation, and coverage targets in `src/recruitsecbench/datasets/partitions.py`, `protocol/partitions.yaml`, and `tests/property/test_partition_isolation.py`
- [ ] T017 [US3] Implement freeze creation, immutable dataset/config/prompt/policy/model/oracle manifests, aggregation compatibility gates, and holdout single-campaign enforcement in `src/recruitsecbench/config/freeze.py`, `src/recruitsecbench/runner/authorization.py`, and `tests/integration/test_freeze_reproducibility.py`

**Checkpoint**: Evaluation and holdout artifacts are sealed and runs cannot combine incompatible evidence.

---

## Phase 6: User Story 4 — Validar a pipeline no AgentDojo padrão (P4)

**Goal**: Establish that the harness works against unmodified standard AgentDojo before interpreting custom-suite results.

**Independent Test**: Run a low-cost standard smoke command and obtain an isolated versioned report; verify complete execution remains explicitly authorized and operational errors remain non-scientific.

- [ ] T018 [US4] Implement the version-pinned standard AgentDojo adapter, namespace isolation, and immutable run metadata capture in `src/recruitsecbench/adapters/agentdojo_standard.py`, `src/recruitsecbench/runner/standard.py`, and `tests/contract/test_agentdojo_standard.py`
- [ ] T019 [US4] Implement standard-suite smoke/full command paths, explicit full-run authorization, budget guardrails, and isolated reports in `src/recruitsecbench/cli/agentdojo.py`, `src/recruitsecbench/runner/budget.py`, and `tests/integration/test_agentdojo_smoke.py`
- [ ] T020 [US4] Implement standard-suite result classification that preserves timeout/cancellation/provider/harness errors outside SAFE/BLOCK/attack outcome metrics in `src/recruitsecbench/runner/classification.py`, `src/recruitsecbench/analysis/namespaces.py`, and `tests/unit/test_operational_failure_separation.py`

**Checkpoint**: Standard AgentDojo is a validated external control, never pooled with RecruitSecBench evidence.

---

## Phase 7: User Story 5 — Executar o baseline RecruitSecBench (P5)

**Goal**: Run the frozen custom suite under C0 with deterministic policy enforcement, independently measured benign utility and attack validity.

**Independent Test**: Execute frozen C0 cases across repetitions using the mock model and retrieve separate utility, attack, policy, leakage, canary, side-effect, state, cost, and latency outcomes.

- [ ] T021 [US5] Implement the deny-by-default ToolGateway with canonical binding, actor/scope/state/allowlist/argument/idempotency/side-effect checks and stable decisions in `src/recruitsecbench/policies/gateway.py`, `src/recruitsecbench/policies/decisions.py`, and `tests/property/test_tool_gateway.py`
- [ ] T022 [US5] Implement the deterministic AgentDojo custom environment, simulated CV/questionnaire/evaluation tools, mock-model adapter, and authority-free data handling in `src/recruitsecbench/agentdojo_suite/`, `src/recruitsecbench/adapters/mock_model.py`, and `tests/integration/test_custom_suite.py`
- [ ] T023 [US5] Implement baseline C0 orchestration with resumable attempts, three repetitions, sanitized event capture, deterministic oracles, and separated outcome records in `src/recruitsecbench/runner/executor.py`, `src/recruitsecbench/runner/baseline.py`, and `tests/integration/test_baseline_c0.py`
- [ ] T024 [US5] Implement the isolated application-backed Compose smoke layer and canonical SmartRH/Agno adapter contract checks without production side effects in `infra/compose/compose.yaml`, `src/recruitsecbench/adapters/smartrh.py`, `src/recruitsecbench/adapters/agno.py`, and `tests/e2e/test_application_smoke.py`

**Checkpoint**: C0 validates benign behavior and valid attacks before any defensive claim is possible.

---

## Phase 8: User Story 6 — Comparar intervenções CaMeL e FIDES (P6)

**Goal**: Apply and evaluate CaMeL and FIDES independently and jointly against the exact frozen baseline protocol.

**Independent Test**: Re-run evaluation cases under C1–C3 and show configuration-compatible paired comparisons that expose security–utility trade-offs.

- [ ] T025 [US6] Reproduce pinned official CaMeL and Microsoft FIDES smoke controls in isolated namespaces, retaining their provenance separately from adapted conditions in `src/recruitsecbench/controls/official.py`, `tests/contract/test_official_controls.py`, and `manifests/official-controls/`
- [ ] T026 [US6] Implement feature-flagged Agno CaMeL and FIDES adaptations with control/data separation, minimization, provenance, and conformance tests in `src/recruitsecbench/controls/camel.py`, `src/recruitsecbench/controls/fides.py`, and `tests/integration/test_control_conformance.py`
- [ ] T027 [US6] Implement C1–C3 factorial execution and paired comparison preparation that fixes cases, seeds, attacks, oracles, and metrics while recording cost/latency/review burden in `src/recruitsecbench/runner/factorial.py`, `src/recruitsecbench/analysis/paired.py`, and `tests/integration/test_factorial_conditions.py`

**Checkpoint**: Each control and their combination are comparable to C0 without holdout-driven tuning.

---

## Phase 9: User Story 7 — Avaliar um auditor em modo sombra (P7)

**Goal**: Measure a non-intervening auditor on minimized traces without exposing deterministic gold information or affecting executions.

**Independent Test**: Run the auditor on authorized sanitized traces, prove its input excludes labels/outcomes, and compute class-level performance against separately managed human references.

- [ ] T028 [US7] Implement the auditor input projection, tool-free shadow runner, and prediction record (decision/category/severity/evidence/confidence) in `src/recruitsecbench/auditor/view.py`, `src/recruitsecbench/auditor/runner.py`, and `tests/property/test_auditor_blindness.py`
- [ ] T029 [US7] Implement blinded two-reviewer annotation exports/imports, immutable original labels, disagreement handling, and adjudication workflow in `src/recruitsecbench/auditor/annotations.py`, `protocol/annotation-guide.md`, and `tests/integration/test_annotation_workflow.py`
- [ ] T030 [US7] Implement auditor evaluation by class, abstention, false-positive/false-negative reporting, and strict separation from deterministic invariant outcomes in `src/recruitsecbench/auditor/metrics.py`, `src/recruitsecbench/analysis/auditor.py`, and `tests/unit/test_auditor_metrics.py`

**Checkpoint**: Auditor results quantify residual semantic risk and cannot alter an experiment or a candidate decision.

---

## Phase 10: User Story 8 — Sincronizar evidência e artigo (P8)

**Goal**: Regenerate analyses and an English manuscript exclusively from traceable evidence, retaining null, failed, and inconclusive results.

**Independent Test**: Navigate any reported number to its `evidence_id`, runs, manifests, and method; regenerate tables/figures without editing values manually and fail claim linting for unsupported conclusions.

- [ ] T031 [US8] Implement immutable raw-to-Parquet analysis ingestion, case-clustered bootstrap, factorial effects, exact/permutation options, Holm correction, and failure retention in `src/recruitsecbench/analysis/ingest.py`, `src/recruitsecbench/analysis/statistics.py`, and `tests/property/test_statistics.py`
- [ ] T032 [US8] Implement evidence records, requirement/case/attack/defense/oracle/metric/claim links, evidence-index generation, and unsupported-claim linting in `src/recruitsecbench/publication/evidence.py`, `src/recruitsecbench/publication/claims.py`, and `tests/integration/test_evidence_traceability.py`
- [ ] T033 [US8] Implement reproducible tables, figures, preliminary-result labeling, limitations reporting, and English Quarto manuscript rendering in `paper/manuscript.qmd`, `src/recruitsecbench/publication/render.py`, and `tests/integration/test_manuscript_render.py`

**Checkpoint**: The manuscript is an evidence-backed artifact that distinguishes objectives, methods, preliminary results, and observed claims.

---

## Phase 11: Polish & cross-cutting release checks

**Purpose**: Verify the assembled artifact, documentation, and release gates without implicitly launching costly or sealed campaigns.

- [ ] T034 [P] Complete the threat model, protocol, data dictionary, attack taxonomy, control matrix, and residual-risk documentation in `protocol/`, `docs/threat-model.md`, and `docs/data-dictionary.md`
- [ ] T035 Run the documented safe validation sequence (doctor, schemas, corpus generation, privacy gate, standard/custom smoke, and manuscript render) and record reproducible results in `specs/002-build-recruitsecbench/quickstart.md`, `tests/e2e/test_quickstart.py`, and `manifests/validation/`
- [ ] T036 Implement pilot preflight and the explicit budget-gated synthetic pilot command (default maximum USD 25, credentials required, no implicit evaluation/holdout) in `src/recruitsecbench/cli/pilot.py`, `src/recruitsecbench/runner/preflight.py`, and `tests/integration/test_pilot_gates.py`
- [ ] T037 Assemble the reproducibility bundle with lockfiles, manifests, hashes, environment capture, validation report, limitations, and promotion/evidence-gate status in `src/recruitsecbench/publication/bundle.py`, `docs/reproducibility.md`, and `tests/integration/test_reproducibility_bundle.py`

---

## Dependencies & execution order

- **Phase 1 → Phase 2**: Setup enables the shared contracts and safety gates.
- **All user stories require Phase 2**. The recommended implementation sequence is US1 → US2 → US3 → US4 → US5 → US6 → US7 → US8 because each step freezes or measures inputs needed by the next.
- **US1–US3** establish governed, valid, frozen artifacts. **US4** is an independent harness control and can run alongside US1–US3 once the foundation exists. **US5** requires US2–US3 and should follow the US4 smoke. **US6** requires C0 from US5. **US7** consumes sanitized run traces from US5/US6. **US8** consumes evidence from completed runs and can start its data pipeline after US5.
- **Phase 11** follows the desired delivery scope; T036 never authorizes an evaluation or holdout run.

## Parallel opportunities

- T002, T003, T005, T006, and T007 can proceed in parallel after T001, as they own separate modules.
- T012–T014 can be developed in parallel once T004 is stable; T015 then integrates their outputs.
- T018–T020 can proceed independently after the foundation because standard AgentDojo has a separate namespace.
- T021 and T024 can proceed in parallel; T022–T023 depend on the ToolGateway and the frozen corpus.
- T025 and T026 can run in parallel, then T027 integrates the controls. T031 can start after the first C0 outputs while US6/US7 continue.

## Implementation strategy

### MVP first

Deliver Phases 1–3 only: the project can govern and safely release/deny derived profiles, which is the non-negotiable privacy gate for all later benchmark work. Validate T011 independently before generating public benchmark data.

### Incremental delivery

1. Add US2 and US3 to produce a fully synthetic, valid, frozen corpus.
2. Add US4 and US5 to establish an external harness control and C0 baseline.
3. Add US6 and US7 for controls and shadow audit.
4. Add US8 and Phase 11 to publish only evidence-supported, reproducible results.

## Format validation

All 37 tasks use the required checkbox, sequential task ID, optional `[P]` marker only where parallelizable, `[US#]` labels for story tasks, and concrete repository paths.

