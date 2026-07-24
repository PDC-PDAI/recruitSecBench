# Data Model: RecruitSecBench

## Modeling rules

- Every entity has a stable canonical ID; product aliases exist only in adapter metadata.
- All records include `schema_version`, `partition`, provenance, and content hash where
  applicable.
- References resolve inside one frozen artifact graph. A lineage connected component
  belongs to exactly one partition.
- Real people and public synthetic candidates never share an identity namespace.
- Timestamps are RFC 3339 UTC. Ordered trace events additionally use an integer sequence.
- Dataset schemas validate shape; cross-record validators enforce relationships, scope,
  state, lineage, and hash invariants.

## Domain entities

### Project

Fields: `project_id`, name, description, scope policy, synthetic flag, provenance.

Relationships:

- owns one or more HiringProcesses;
- defines the outer authorization boundary;
- has zero or more authorized Actors.

### HiringProcess

Fields: `hiring_process_id`, `project_id`, code, title, status, start/end dates,
description.

Relationships:

- belongs to exactly one Project;
- owns one or more Vacancies;
- status is `DRAFT | ACTIVE | CLOSED`.

### Vacancy

Canonical counterpart of SmartRH `HiringProcessOpening`.

Fields: `vacancy_id`, `hiring_process_id`, title, description, seniority, location
bucket, requirements, competencies, EvaluationCriteria, weights, status, variant ID.

Relationships:

- belongs to one HiringProcess;
- receives Applications;
- owns Questionnaires;
- may have synthetic injection-bearing variants.

Validation:

- criterion IDs are unique per vacancy;
- weights are positive and sum to the frozen scale;
- variant records preserve the base vacancy linkage;
- `vaga_id`, `job_opening_id`, and `openingId` are forbidden as canonical fields.

### Candidate

Fields: `candidate_id`, source class `SYNTHETIC | REAL_DERIVED`, anonymized profile
label, professional area, seniority, language, partition lineage, privacy status.

Validation:

- no email, phone, public user ID, name, or source URL is used as the ID;
- `REAL_DERIVED` candidates cannot enter public artifacts;
- a candidate and all connected CVs/applications remain in one partition.

### ProfessionalDocument

Fields: `document_id`, `candidate_id`, document type, language, synthetic/derived text,
structured skills, generalized experiences, generalized education, canary references,
privacy review ID, source lineage ID.

Validation:

- original bytes and original text are never fields;
- public records must be `SYNTHETIC`;
- real derivatives require `APPROVED_CONTROLLED` before controlled experimental use.

### Application

Fields: `application_id`, `candidate_id`, `vacancy_id`, derived
`hiring_process_id`, current evaluation state, state history, authorization scope,
questionnaire IDs, permission profile, round token.

Relationships:

- joins exactly one Candidate and one Vacancy;
- inherits process and project through Vacancy;
- owns CandidateResponses and evaluation outcomes.

Canonical evaluation states:

```text
PENDENTE
  ├── DOCUMENTOS_INDEXADOS
  │     ├── EM_AVALIACAO
  │     │     ├── CONCLUIDO  (only atomic save with scores)
  │     │     ├── FALHOU
  │     │     └── PENDENTE   (guarded operational redispatch)
  │     ├── FALHOU
  │     └── PENDENTE
  └── FALHOU

CONCLUIDO ──> PENDENTE
FALHOU    ──> PENDENTE
```

Retries of the same transition are idempotent. Concurrent or stale round tokens are
rejected without side effects.

### Questionnaire

Fields: `questionnaire_id`, `vacancy_id`, optional `application_id`, derived process
and project IDs, version, purpose, editorial status, generation status, author/agent,
scope, criterion IDs, ordered question IDs, access/update rules, generation metadata,
approval metadata.

Relationships:

- belongs to one Vacancy and optionally one compatible Application;
- contains one or more Questions;
- may have many versions, but responses retain their original version.

Editorial states:

```text
DRAFT ──> PUBLISHED ──> ARCHIVED
```

Generation states are orthogonal:

```text
null (manual)
GENERATING ──> READY
           └─> FAILED
```

Rules:

- only one published questionnaire per vacancy;
- publishing requires at least one valid question;
- generation save requires `GENERATING`;
- editing content/weights is allowed only in `DRAFT` with an authorized actor;
- an application-linked questionnaire must share vacancy, process, and project ancestry.

### Question

Fields: `question_id`, `questionnaire_id`, text, description, response type, subtype,
competency/criterion ID, relevance rationale, required flag, order, expected rubric,
privacy restrictions, weight, origin, review status.

Response types: `SHORT_TEXT | LONG_TEXT | FILE_UPLOAD`. Additional benchmark-only types
must be explicitly versioned rather than silently mapped to product types.

Validation:

- order is unique and contiguous within a version;
- weight is bounded by the contract;
- criterion belongs to the questionnaire vacancy;
- text must not request prohibited personal data;
- generated questions carry rationale and review status.

### CandidateResponse

Fields: `response_id`, `application_id`, `candidate_id`, `vacancy_id`,
`questionnaire_id`, `question_id`, text or synthetic file reference, expected quality,
adversarial marker, immutable creation metadata.

Validation:

- all six ancestry references agree;
- the question belongs to the referenced questionnaire version;
- one answer exists per application/question unless a fixture explicitly models a
  duplicate-write attack;
- public files contain only synthetic content.

### EvaluationCriterion and EvaluationOutcome

Criterion fields: `criterion_id`, vacancy ID, competency, description, weight, rubric,
privacy restrictions.

Outcome fields: `evaluation_id`, application ID, dimension, score, justification,
evidence references, weights used, generated time, model/configuration reference.

Validation:

- scores remain benchmark observations and never drive real employment decisions;
- evidence may refer only to documents/questions authorized for the application;
- aggregate score weights match the frozen vacancy criteria.

### Actor, AuthorizationScope, AgentSession, Tool

Actor fields: actor ID, role, synthetic identity, allowed project/process/vacancy scope.

Scope fields: project ID and optional process, vacancy, application, candidate,
questionnaire, and session IDs.

Session fields: `session_id`, actor ID, scope, agent ID, created/expires timestamps,
memory references, replay lineage, status.

Tool fields: `tool_id`, canonical name, product name, input/output schema versions,
allowed stages, side-effect class, idempotency policy, data-flow source/sink labels.

Rules:

- a narrower scope must be a valid descendant of every broader ID;
- sessions cannot be reused across actors or scope lineages;
- tool availability is stage-specific and deny-by-default.

## Privacy and provenance entities

### SourceDocumentRecord

Stored only in the external restricted area.

Fields: opaque source ID, local relative path, byte hash, origin, specific purpose,
controller, responsible person, legal basis/authorization evidence, privacy/ethics
approval status, retention deadline, revocation policy, ingestion status.

### PrivacyAnalysis

Fields: analysis ID, source ID, tool/model versions, detected PII categories and counts,
normalized common-span length, semantic similarity, quasi-identifier tuple,
equivalence-class size, structural validation, automatic decision, reason codes.

Automatic approval thresholds are all conjunctive:

- zero PII/identifier findings;
- longest normalized common span <= 8 tokens;
- semantic similarity <= 0.80;
- quasi-identifier equivalence class k >= 5;
- structural validation passes.

Automatic success creates `PENDING_HUMAN_REVIEW`, never final release.

### HumanPrivacyReview

Fields: review ID, privacy analysis ID, reviewer pseudonymous ID, role
`PRIMARY | SECONDARY`, decision, uncertainty flag, reason codes, timestamp, signature or
attestation hash.

Rules:

- every real derivative requires one primary approval;
- uncertain cases require an independent secondary approval;
- original reviewer decisions are immutable;
- implementation automation cannot manufacture these records.

### QuarantineRecord

Fields: source/derivative IDs, trigger, discovered time, effective time, affected artifact
and run IDs, tombstone hash, remediation status.

Quarantine removes content from usable/public views, invalidates affected releases, and
retains only allowed technical tombstones and proven non-identifiable aggregates.

## Dataset entities

### DomainRecord

Discriminated by `record_type`:
`project | hiring_process | vacancy | candidate | cv | application | questionnaire |
question | candidate_response | agent_session | tool | process_state |
evaluation_criterion | evaluation_outcome`.

Each subtype has a canonical content object and references the same lineage ID.

### BenignCase

Fields: case ID, task family, actor, scope, input record IDs, fixture IDs, initial state,
request, allowed tools/operations/data, expected ALLOW decision, utility oracles, valid
end states, maximum side effects, primary metrics.

Task families:

- questionnaire generation/management;
- CV search;
- CV search chat;
- candidate evaluation;
- RAG retrieval;
- tool execution;
- state transition;
- response analysis.

### AdversarialCase

Fields: case ID, benign counterpart, attack family, target surface, placement, payload
template, prerequisites, validity oracle, prohibited outcome, severity, expected policy
decision, attack-success oracles, evidence requirements.

Target surfaces include vacancy, CV, application, questionnaire, question, response, RAG,
session, tool, MCP, state, and auditor.

### DeterministicFixture

Kinds: tool call, ID binding, relationship graph, state transition, scope access,
permission, session, and canary.

Every operation declares actor, current state, arguments, expected decision/reason,
normalized arguments, next state, and expected side-effect count.

### Canary

Fields: canary ID, synthetic token and hash, owner scope, authorized actors, source record,
JSON pointer, detection stages, match mode.

Detection stages: retrieval, context, tool argument, tool result, output, trace.

### AuditTrace

Fields: trace ID, run ID, case ID, condition, repetition, model/config, seed, execution
status, ordered TraceEvents, tool calls, policy decisions, state transitions, side effects,
canary observations, deterministic outcomes, separate human annotations, separate auditor
prediction, and sanitized auditor view.

Forbidden trace content:

- original or real-derived CV text;
- direct PII or live credentials;
- unrestricted prompt bodies;
- human labels or deterministic outcomes inside the auditor view.

## Experiment and evidence entities

### ExperimentConfiguration

Fields: experiment ID/version, benchmark namespace, partition, case manifest hashes,
condition, model, provider settings, seed set, repetitions, attack/defense versions,
policy/prompt/tool schema hashes, timeout/retry taxonomy, cost ceiling, commit snapshots.

Conditions:

| ID | CaMeL adaptation | FIDES adaptation |
|---|---:|---:|
| C0 | off | off |
| C1 | on | off |
| C2 | off | on |
| C3 | on | on |

### Attempt and Run

An Attempt is one physical execution. A Run groups attempts for one
case/condition/model/repetition key.

Attempt statuses:
`completed | provider_error | transport_error | harness_error | timeout | cancelled |
budget_blocked | invalid_case | inconclusive`.

Only a completed attempt is evaluated by scientific oracles. Every retry references its
predecessor and reason. Attempts are never overwritten.

### PolicyDecision and SideEffect

PolicyDecision fields: decision ID, event sequence, ALLOW/DENY/HUMAN_REVIEW/ERROR, stable
reason code, normalized arguments hash, governing policy version.

SideEffect fields: effect ID, tool, resource ID, operation, before/after hashes,
idempotency key, committed flag, rollback reference.

### AuditorPrediction, HumanAnnotation, Adjudication

AuditorPrediction: trace/view hashes, decision, category, severity, short evidence,
confidence, auditor model/config.

HumanAnnotation: independent annotator ID, decision, category, severity, evidence,
timestamp; stored outside the auditor view.

Adjudication: references all original annotations, final label, adjudicator, rationale,
timestamp; never replaces annotations.

### EvidenceRecord and ClaimLink

EvidenceRecord fields: evidence ID, research question, metric, analysis version, input
manifest/run hashes, output table/figure paths, status, limitations.

ClaimLink fields: claim ID, manuscript section, type
`OBJECTIVE | HYPOTHESIS | METHOD | OBSERVED_RESULT | INTERPRETATION | LIMITATION`,
evidence IDs, validation status.

Observed-result language is invalid without at least one compatible completed evidence
record.

## Referential and partition invariants

1. Project ancestry resolves for every scoped entity and operation.
2. Application candidate/vacancy/process/project references agree.
3. Questionnaire/application links share vacancy, process, and project.
4. Response references agree across candidate, application, vacancy, questionnaire, and
   question.
5. Tool arguments use canonical IDs after normalization and preserve the submitted alias
   map in sanitized adapter metadata.
6. A connected lineage cannot cross development, pilot, evaluation, or holdout.
7. Evaluation and holdout manifest hashes are immutable after freeze.
8. Event sequences are unique and strictly increasing per attempt.
9. Side effects never exceed the case limit; rejected calls have zero committed effects.
10. Standard AgentDojo, official-control reproduction, simulator, and application-backed
    evidence remain in separate namespaces and are never silently pooled.
