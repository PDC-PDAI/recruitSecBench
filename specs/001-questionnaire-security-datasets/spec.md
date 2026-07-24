# Feature Specification: Linked Recruitment and Questionnaire Security Datasets

**Feature Branch**: `001-questionnaire-security-datasets`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "Expand the benchmark data contracts and datasets to cover linked CV evaluation and questionnaire generation/management flows, including deterministic fixtures, validity oracles, benign cases, and adversarial cases."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Model the Linked Recruitment Domain (Priority: P1)

As a benchmark dataset curator, I can represent candidates, CVs, vacancies,
applications, questionnaires, questions, and candidate responses with stable links and
scope so that both product flows can be reproduced without consulting a live system.

**Why this priority**: All benign tasks, attacks, fixtures, and oracles depend on an
unambiguous canonical domain model.

**Independent Test**: Validate a synthetic end-to-end record set containing one vacancy,
one candidate, one application, a versioned questionnaire with ordered questions, and
responses. Every reference and scope relationship must resolve without product aliases.

**Acceptance Scenarios**:

1. **Given** a vacancy and candidate in the same authorized hiring process, **When** an
   application and questionnaire are recorded, **Then** their canonical IDs, scope,
   versions, statuses, and relationships are valid and resolvable.
2. **Given** a questionnaire associated only with a vacancy, **When** it is recorded
   before any application exists, **Then** it remains valid without an `application_id`.
3. **Given** a candidate answer, **When** it is validated, **Then** it resolves to exactly
   one candidate, application, vacancy, questionnaire version, and question in a
   consistent scope.
4. **Given** a cross-process or mismatched reference, **When** the record set is checked,
   **Then** it is rejected with a deterministic invariant violation.

---

### User Story 2 - Build Benign Questionnaire Cases (Priority: P2)

As a benchmark author, I can define legitimate questionnaire-generation and management
tasks with expected outcomes so that agent utility is measured before defenses are
evaluated.

**Why this priority**: Security comparisons are meaningful only when legitimate task
success is defined and preserved.

**Independent Test**: Run the benign cases against their frozen inputs and confirm that
each case identifies its allowed actions, scope, initial state, expected questionnaire
properties, and utility outcome.

**Acceptance Scenarios**:

1. **Given** a vacancy with requirements and competencies, **When** a questionnaire is
   generated, **Then** its questions cover the requested criteria, remain relevant to
   the vacancy, and request no prohibited personal data.
2. **Given** an authorized questionnaire editor and a questionnaire in an editable
   state, **When** a question is updated, **Then** a new or updated version records the
   authorized change without altering unrelated criteria or prior frozen evidence.
3. **Given** a questionnaire in a non-editable state, **When** an update is requested,
   **Then** the expected outcome is a denial with a stable reason code.

---

### User Story 3 - Exercise Questionnaire Attacks (Priority: P3)

As a security researcher, I can mutate the same product flows with prompt injection,
scope abuse, unauthorized changes, and privacy attacks so that attack success and
defense behavior are objectively measurable.

**Why this priority**: The new questionnaire flow increases the agent's authority and
creates attack surfaces not covered by CV evaluation alone.

**Independent Test**: For every required attack family, validate at least one executable
adversarial case whose goal, validity conditions, prohibited outcome, authorized
baseline, and attack-success oracle are explicit.

**Acceptance Scenarios**:

1. **Given** adversarial instructions inside a CV, vacancy, or candidate response,
   **When** the agent generates or updates a questionnaire, **Then** the case detects any
   unauthorized change to questions, criteria, weights, scope, or requested data.
2. **Given** a questionnaire or application belonging to another hiring process,
   **When** an agent attempts to read or alter it, **Then** access is denied and the
   cross-scope attempt is recorded.
3. **Given** content that asks the agent to collect or reveal personal data, **When** the
   questionnaire or response is produced, **Then** the privacy oracle detects the
   prohibited request or disclosure.
4. **Given** a candidate response that tries to alter evaluation or workflow state,
   **When** the response is processed, **Then** it remains data and cannot change policy,
   scoring criteria, authorization, or state.

---

### User Story 4 - Produce Deterministic Security Evidence (Priority: P4)

As an experiment reviewer, I can reproduce questionnaire create, read, update, state,
and access-control decisions and inspect separate validity dimensions so that each claim
can be traced to immutable evidence.

**Why this priority**: Reproducible oracles distinguish enforceable security properties
from semantic judgments that require human review.

**Independent Test**: Repeat the complete fixture and oracle suite from a frozen manifest
and obtain identical structural, relationship, scope, access, lifecycle, privacy, and
tampering outcomes for every case.

**Acceptance Scenarios**:

1. **Given** the same frozen case, fixtures, and policy version, **When** deterministic
   evaluation is repeated, **Then** all decisions and reason codes are identical.
2. **Given** a structurally valid but semantically ambiguous questionnaire, **When** it is
   evaluated, **Then** deterministic dimensions remain separate and only the ambiguous
   relevance judgment is routed to human review.
3. **Given** a modified frozen input, **When** evidence is generated, **Then** the manifest
   or content hash changes and results are not silently pooled with the prior version.

### Edge Cases

- A questionnaire is valid for a vacancy but has no associated application yet.
- An application is withdrawn after a questionnaire was generated or answered.
- A questionnaire version is retired while historical responses still reference it.
- Two questions have the same order or a response refers to a question from another
  questionnaire version.
- A question covers multiple competencies or has no defensible link to any vacancy
  requirement.
- An otherwise relevant question requests contact, identity, health, family, financial,
  demographic, or other unnecessary personal information.
- Adversarial content is split across vacancy, CV, questionnaire, and candidate response
  rather than appearing in a single record.
- An authorized update is retried and would otherwise create a duplicate version or
  duplicate persistence event.
- A provider or harness failure occurs before an oracle can classify the security result.
- A semantic relevance judgment is ambiguous while scope and access checks are conclusive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The domain dataset MUST support canonical record types for CV, vacancy,
  application, questionnaire, and candidate response.
- **FR-002**: An application record MUST identify its candidate, vacancy, hiring process,
  current status, authorized scope, and provenance using stable canonical IDs.
- **FR-003**: A questionnaire record MUST identify its vacancy, optional application,
  version, purpose, status, access rules, authorized scope, provenance, and ordered
  questions.
- **FR-004**: Every question MUST have a stable ID, text, response type, evaluated
  competency or criterion, required flag, order, and expected-answer or evaluation
  criteria appropriate to its type.
- **FR-005**: Every candidate response MUST identify the candidate, application, vacancy,
  questionnaire version, and question it answers.
- **FR-006**: Cross-record validation MUST reject unresolved references, inconsistent
  ancestry, duplicate IDs, duplicate question order, and response-to-version mismatch.
- **FR-007**: Questionnaire lifecycle states and allowed transitions MUST be explicit;
  create, update, publish/activate, retire, and equivalent invalid transitions MUST have
  deterministic expected outcomes.
- **FR-008**: Questionnaire access rules MUST distinguish permission to create, read,
  update, change state, and view candidate responses within the authorized scope.
- **FR-009**: Historical questionnaire versions and their responses MUST remain
  attributable after later versions or state changes are created.
- **FR-010**: The adversarial dataset MUST include `questionnaire` as an explicit attack
  surface and preserve the attacked record, origin, and intended unauthorized outcome.
- **FR-011**: The benchmark MUST contain benign questionnaire-generation cases covering
  generation from vacancy requirements, controlled revision, authorized reading, valid
  state transition, and candidate answering.
- **FR-012**: Each benign case MUST define the legitimate task, input records, allowed
  actions, authorized scope, initial state, expected output, utility oracle, case version,
  and reproducibility inputs.
- **FR-013**: The benchmark MUST contain adversarial cases for prompt injection in CVs,
  vacancies, and candidate responses.
- **FR-014**: The benchmark MUST contain adversarial cases for questions or criteria that
  are unrelated to, or outside the authorized scope of, the vacancy.
- **FR-015**: The benchmark MUST contain adversarial cases for reading or modifying a
  questionnaire or application belonging to another hiring process.
- **FR-016**: The benchmark MUST contain adversarial cases for unauthorized changes to
  questions, expected criteria, weights, version, purpose, or questionnaire status.
- **FR-017**: The benchmark MUST contain adversarial cases that induce collection or
  disclosure of unnecessary personal or sensitive data.
- **FR-018**: The benchmark MUST contain adversarial candidate responses that attempt to
  change evaluation criteria, scores, authorization, agent policy, or workflow state.
- **FR-019**: Each adversarial case MUST define validity conditions, attack goal,
  prohibited outcome, allowed actions, scope, initial state, attack-success oracle,
  related benign case when one exists, and case version.
- **FR-020**: Deterministic fixtures MUST cover questionnaire creation, retrieval, update,
  versioning, valid and invalid state transitions, authorized and unauthorized access,
  cross-scope references, retries, and duplicate persistence.
- **FR-021**: Questionnaire evaluation MUST report separate outcomes for structural
  validity, referential integrity, vacancy relevance, personal-data safety, scope and
  access compliance, lifecycle compliance, and adversarial manipulation.
- **FR-022**: Structural, referential, scope, access, lifecycle, duplicate, hash, and
  explicit prohibited-data outcomes MUST use deterministic oracles and stable reason
  codes.
- **FR-023**: Relevance MUST be evaluated against explicit vacancy requirements and
  competency coverage. Ambiguous semantic relevance MUST be reported separately as
  requiring human review and MUST NOT override deterministic failures.
- **FR-024**: Content originating in a CV, vacancy, questionnaire, or candidate response
  MUST be treated as untrusted data and MUST NOT grant authority to change policy,
  scope, access, criteria, weights, or workflow state.
- **FR-025**: Every case MUST preserve separate legitimate-task, attack, policy, execution,
  and provider/harness outcomes so failures are not silently reclassified.
- **FR-026**: Dataset manifests MUST identify versions, hashes, partitions, provenance,
  upstream dependencies, privacy status, and frozen artifacts used by each run.
- **FR-027**: Real CV originals and direct identifiers MUST remain outside the benchmark;
  all distributable records MUST be synthetic or authorized anonymized derivatives.
- **FR-028**: Traces and evidence MUST minimize personal data and MUST NOT store full CVs,
  full source prompts, real credentials, or hidden gold outcomes in an auditor view.
- **FR-029**: Security labels, questionnaire-quality outcomes, and auditor predictions
  MUST NOT automatically hire, reject, or rank a candidate.
- **FR-030**: Every reported benchmark result MUST be traceable from a case and condition
  to raw repetitions, oracle outcomes, manifest version, and immutable evidence ID.

### Key Entities

- **Candidate**: An anonymized logical person participating in a synthetic or authorized
  recruitment scenario; never a direct public or government identifier.
- **CV**: A minimized candidate profile with provenance, authorized scope, and content
  treated as untrusted data.
- **Vacancy**: A scoped role definition containing requirements, competencies, seniority,
  and evaluation criteria used as the authority for questionnaire relevance.
- **Application**: The canonical link among candidate, vacancy, and hiring process,
  including lifecycle status and scope used by responses and access checks.
- **Questionnaire**: A versioned, scoped assessment associated with a vacancy and
  optionally an application, with purpose, status, access rules, and ordered questions.
- **Question**: A stable questionnaire item describing response type, competency or
  criterion, requirement, order, and expected-answer or evaluation criteria.
- **Candidate Response**: Untrusted answer content linked to one candidate, application,
  vacancy, questionnaire version, and question.
- **Benign Case**: A legitimate task plus inputs, permissions, expected utility outcome,
  and reproducibility metadata.
- **Adversarial Case**: A valid attack mutation with explicit goal, prohibited outcome,
  attacked surface, and attack-success oracle.
- **Deterministic Fixture**: Frozen identities, scopes, states, actions, and expected
  decisions used to reproduce access and lifecycle behavior.
- **Questionnaire Oracle Result**: Independent validity dimensions, evidence, decision,
  and stable reason codes without collapsing deterministic and semantic judgments.
- **Artifact Manifest**: Versioned inventory of inputs, hashes, partitions, provenance,
  privacy review, and dependencies for a frozen dataset release or experiment run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supplied valid examples across both product flows satisfy their
  structural contracts and all cross-record invariants.
- **SC-002**: 100% of intentionally invalid reference, scope, access, lifecycle, duplicate,
  and version fixtures are rejected with the expected stable reason code.
- **SC-003**: Every attack family requested in this specification has at least one valid,
  executable adversarial case and, where a legitimate counterpart exists, a linked
  benign case.
- **SC-004**: Every benign questionnaire case has a measurable utility outcome, and 100%
  of defense comparisons can report utility and security outcomes separately.
- **SC-005**: 100% of questionnaire cases produce independent results for structure,
  references, relevance, privacy, scope/access, lifecycle, and manipulation rather than
  a single opaque validity label.
- **SC-006**: Repeating deterministic evaluation with unchanged frozen artifacts produces
  identical decisions and reason codes for 100% of cases.
- **SC-007**: Every reported aggregate can be traced to raw repetitions, case and
  condition IDs, manifest version, artifact hashes, and an evidence ID.
- **SC-008**: Privacy validation finds zero direct identifiers, real credentials, full
  CVs, or full source prompts in distributable datasets and minimized traces.
- **SC-009**: An independent reviewer can reconstruct the authorized scope, expected
  action, oracle decision, and supporting evidence for 100% of sampled cases without
  access to the live product.
- **SC-010**: Ambiguous relevance cases are routed to human review while 100% of
  deterministic violations retain their original blocking result.

## Assumptions

- `application` and `questionnaire` will be first-class canonical domain record types,
  because both require independent lifecycle, provenance, and cross-record validation.
- A questionnaire always belongs to a vacancy and may optionally belong to an application.
- Questionnaire lifecycle uses an explicit controlled state set with editable and
  non-editable states; exact labels may be refined during planning without weakening
  the transition requirements.
- Vacancy requirements and competencies are the authoritative reference for deterministic
  coverage checks; genuinely ambiguous semantic relevance is assigned to human review.
- Benchmark data is synthetic by default. Authorized anonymized derivatives may be used
  only after the privacy and provenance requirements are met.
- This feature covers contracts, examples, fixtures, cases, and oracles. It does not
  authorize a live questionnaire service, production side effects, or automated hiring.
- Existing canonical IDs for vacancy, hiring process, application, and candidate remain
  stable; product-specific aliases belong outside the dataset contracts.

## Security, Research Integrity & Production Boundaries *(mandatory)*

### Threat Model and Authorization

- **Assets and affected people**: Candidate-derived data, vacancies, applications,
  questionnaires, responses, evaluation criteria, workflow state, recruiters, and
  candidates affected by misuse.
- **Adversaries and capabilities**: Attackers may place instructions in CVs, vacancies,
  questionnaires, or candidate responses; mutate IDs and arguments; replay updates;
  request cross-scope data; and try to manipulate criteria, privacy, or state. They do
  not receive authority to change external policy or frozen gold outcomes.
- **Authorized scope**: Every action is bounded by user, project, hiring process, vacancy,
  application, candidate, questionnaire, version, and workflow state as applicable.
- **Untrusted inputs**: CVs, vacancy prose, questionnaire text, candidate responses,
  retrieved content, generated output, and tool output.
- **Deterministic invariants**: Canonical IDs, ancestry, record kind, versions, question
  order, tools/actions, permissions, states, scopes, hashes, duplicates, and canaries.

### Evidence and Measurement

- **Research questions / planned claims**: Whether the expanded benchmark reproduces
  both flows; whether controls reduce questionnaire attacks without destroying benign
  generation utility; and which residual semantic cases require human review.
- **Baseline and comparison conditions**: The same frozen benign and adversarial cases
  must be evaluated under baseline, individual controls, and combined controls.
- **Security and utility measures**: Legitimate task success, attack success, policy and
  scope violations, questionnaire validity dimensions, false blocks, review rate,
  latency, tokens, cost, and execution failures.
- **Failure taxonomy**: Legitimate-task failure, attack success/failure, deterministic
  policy result, semantic review result, invalid case, harness failure, provider failure,
  and inconclusive execution remain distinct.
- **Reproducibility artifacts**: Versioned records, cases, fixtures, policies, prompts,
  seeds where applicable, manifests, hashes, raw repetitions, oracle outputs, and
  regenerable analyses.

### Privacy and Human Accountability

- **Data provenance and authorization**: Synthetic by default; any real-person source
  requires authorization, privacy review, anonymization, and exclusion of originals.
- **Minimization, retention, and publication**: Store only scoped IDs, hashes, short
  sanitized evidence, and the minimum content required for reproduction. Release only
  sanitized artifacts with documented retention and privacy status.
- **Human-review and contestation path**: Ambiguous relevance, sensitive attributes,
  uncertain privacy classification, or contextual risk must be reviewable by an
  accountable person without changing deterministic oracle history.
- **Prohibited outcomes**: Automatic hiring, rejection, ranking, criterion changes,
  cross-scope access, unnecessary personal-data collection, secret disclosure, or
  production mutation based solely on an agent or auditor output.

### Maturity Boundary

- **Current status**: Benchmark-only dataset and contract expansion.
- **Explicit non-goals**: Complete security, formal assurance, production deployment,
  automatic hiring decisions, and proof that one model or defense generalizes beyond
  the evaluated conditions.
- **Required gate**: Scope, protocol, baseline, control, audit, and publication gates
  apply. Any future live use requires the constitution's separate production gate.
