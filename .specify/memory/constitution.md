<!--
Scope clarification (2026-09-15): questionnaire generation and answer evaluation only.
Removed the obsolete combined-workflow specs; governance principles are unchanged.

Original Sync Impact Report
- Version change: template (unratified) -> 1.0.0
- Modified principles:
  - Placeholder Principle 1 -> I. Evidence Before Claims
  - Placeholder Principle 2 -> II. Security and Utility Are Measured Together
  - Placeholder Principle 3 -> III. Deterministic Enforcement and Least Authority
  - Placeholder Principle 4 -> IV. Scope Isolation, Privacy, and Data Minimization
  - Placeholder Principle 5 -> V. Human Accountability for High-Stakes Outcomes
- Added principles:
  - VI. Reproducible Artifacts and Explicit Production Promotion
- Added sections:
  - Benchmark Safety and Experimental Boundaries
  - Evidence-Gated Development Workflow
- Removed sections: none; template placeholders were concretized.
- Templates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ✅ .agents/skills/speckit-tasks/SKILL.md
  - ✅ .github/skills/speckit-tasks/SKILL.md
- Runtime guidance reviewed:
  - ✅ README.md
- Follow-up TODOs: none.
-->
# RecruitSecBench Constitution

The implemented research scope is synthetic questionnaire generation and candidate-answer
evaluation, with baseline, FIDES-inspired and CaMeL-inspired variants.

## Core Principles

### I. Evidence Before Claims
Every scientific or security claim MUST identify the research question, threat model,
metric, comparison, and immutable evidence artifact that can support or refute it.
Questions, hypotheses, protocols, stopping rules, and analysis methods MUST be recorded
before the corresponding confirmatory run. Every reported number MUST trace through an
`evidence_id` to retained raw repetitions and a regenerable analysis. Negative,
inconclusive, provider-failure, and hypothesis-refuting results MUST remain in the
record; they MUST NOT be silently removed or reclassified. Exploratory analyses MUST
be labeled as exploratory. This prevents a benchmark from becoming a demonstration
whose conclusions were selected after observing the outputs.

### II. Security and Utility Are Measured Together
Every defense MUST be evaluated against the same versioned benign and adversarial case
suite as its baseline. A result MUST report both legitimate task success and attack or
policy-violation outcomes; a security gain that destroys task utility MUST be presented
as a trade-off. Cases MUST define stable IDs, inputs, seeds where applicable, authorized
scope, initial state, expected result, and success oracles. Tools, IDs, relationships,
states, scopes, schemas, hashes, and canaries MUST use deterministic oracles. Semantic
judgment MAY supplement but MUST NOT replace those oracles. Analysis MUST preserve each
repetition, separate provider or harness failures from security outcomes, aggregate by
`case_id`, quantify uncertainty, and report relevant latency, token, cost, and human-
review overhead. These rules make comparisons reproducible and resistant to inflated
sample counts or subjective scoring.

### III. Deterministic Enforcement and Least Authority
Vacancies, coordinator commands, candidate answers, model output, and tool output
MUST be treated as untrusted data, never as authority to change policy, identity,
scope, state, or permissions. Authorization MUST occur outside the model. Each agent
and workflow stage MUST have an explicit tool allowlist, validated identity and ID
bindings, valid state transitions, bounded arguments, and deny-by-default behavior.
Rejected actions MUST produce a stable reason code. No LLM, prompt, auditor, or
retrieved document MAY override deterministic policy. In production-oriented code,
side effects MUST additionally be authenticated, idempotent where applicable, and
auditable. This limits an agent's power even when its context is compromised.

### IV. Scope Isolation, Privacy, and Data Minimization
Every retrieval, session, rerank, tool call, trace, and persistence operation MUST
enforce the authorized user, project, hiring process, vacancy, application, and
candidate scope that applies to it. Cross-scope relationships MUST be checked before
data is read or written. Benchmark data MUST be synthetic by default. Any source based
on real people requires documented authorization, privacy review, anonymization, and
separation of originals from the harness and public repository. Prompts, traces, and
audit records MUST contain the minimum evidence needed; full personal records, direct identifiers,
real secrets, and unnecessary sensitive attributes MUST NOT be stored. Canaries MUST
be synthetic markers. Published artifacts MUST be sanitized and attacks MUST run only
in controlled environments. This reduces harm to candidates and limits breach impact.

### V. Human Accountability for High-Stakes Outcomes
RecruitSecBench MUST NOT turn security labels, auditor outputs, or benchmark scores into
automatic hiring, rejection, ranking, or employment decisions. Deterministic checks
decide only properties they can prove; ambiguous, contextual, fairness-related, or
sensitive cases MUST be eligible for `HUMAN_REVIEW`. An LLM auditor MUST begin in
shadow mode and MAY become an operational gate only after versioned evaluation against
independent human labels, documented error analysis, acceptable class support, and an
approved governance change. Adjudication MUST preserve original labels and disagreement.
Any future production use MUST define accountable owners, reviewer guidance, explanations,
and a contestation or correction path for affected people. Human review is a governed
safeguard, not a label used to conceal unresolved automation risk.

### VI. Reproducible Artifacts and Explicit Production Promotion
Datasets, cases, prompts, policies, models, provider settings, code, environment, and
analysis scripts used in a run MUST be versioned. Frozen artifacts MUST have manifests,
content hashes, provenance, dependencies, and privacy status. Changing any frozen input
MUST create a new version; results from incompatible versions MUST NOT be silently
pooled. A benchmark prototype MUST NOT be represented as production-ready. Promotion
to production requires a separately approved threat model, privacy and legal assessment,
access review, adversarial regression suite, operational SLOs, monitoring, incident and
rollback procedures, retention rules, and documented residual-risk acceptance. This
preserves scientific reproducibility while making the future production boundary
explicit and reviewable.

## Benchmark Safety and Experimental Boundaries

- The benchmark MUST evaluate scoped, testable properties; it MUST NOT claim complete
  security, formal assurance, or faithful reproduction of a cited system without the
  corresponding evidence.
- Baseline and controls MUST run under comparable, recorded conditions. Material prompt,
  policy, model, dataset, or infrastructure changes require a new manifest and rerun.
- Attack payloads, canaries, identities, vacancies, and neighboring scopes MUST be
  synthetic or explicitly authorized. Live credentials and production side effects are
  prohibited in benchmark fixtures.
- The auditor is restricted to residual semantic risk. It MUST NOT score deterministic
  invariants or receive gold labels, deterministic outcomes, or hidden evaluation data
  in its input view.
- Security events MUST be observable with minimized structured traces, stable reason
  codes, and enough provenance to reconstruct the decision without exposing full source
  documents.
- External standards and related work inform the threat model but do not substitute for
  project-specific requirements, evidence, ethics review, or applicable law.

## Evidence-Gated Development Workflow

1. **Scope gate**: define the legitimate task, stakeholders, assets, adversary,
   authorization boundaries, misuse risks, production status, and explicit exclusions.
2. **Protocol gate**: freeze versioned cases, fixtures, oracles, metrics, repetitions,
   failure taxonomy, statistical method, privacy review, and evidence IDs before the
   confirmatory run.
3. **Baseline gate**: demonstrate valid benign behavior and valid attacks. If attacks do
   not exercise the stated threat model, revise the cases before making defense claims.
4. **Control gate**: test each control independently and in combination against the same
   suite. Record regressions, false blocks, bypasses, cost, latency, and review burden.
5. **Audit gate**: validate semantic labels against independent human review while keeping
   the auditor in shadow mode until Principle V is satisfied.
6. **Publication gate**: regenerate every table and figure from immutable raw outputs;
   connect claims to evidence; disclose limitations, deviations, failures, privacy
   measures, and threats to validity.
7. **Production gate**: satisfy Principle VI through a separate approval. Passing the
   publication gate does not authorize deployment.

Specifications and plans MUST state which gates apply. Tasks that change schemas,
oracles, policies, retrieval scope, traces, metrics, or side effects MUST include tests
and artifact/version updates. Reviews MUST reject unexplained constitution violations;
complexity exceptions require a written rationale and a safer alternative analysis.

## Governance

This constitution is the highest-priority project governance document. Specs, plans,
tasks, schemas, experiments, code, papers, and deployment proposals MUST comply with it.
When artifacts conflict, the more protective constitutional rule prevails until an
amendment is ratified.

Amendments require a written proposal describing the motivation, affected principles,
migration or rerun impact, privacy and safety impact, and approver. Approval requires at
least one project maintainer and, for changes affecting human data, hiring outcomes, or
production promotion, an accountable privacy, legal, ethics, or security reviewer as
appropriate. Emergency protections MAY be tightened immediately, but MUST be documented
and reviewed before results produced under the change are published or pooled.

Versions follow semantic versioning: MAJOR for incompatible removals or redefinitions of
governance guarantees, MINOR for new principles or materially expanded obligations, and
PATCH for non-semantic clarification. Every amendment MUST update the Sync Impact Report,
version, and amendment date, then propagate changes to dependent templates and runtime
guidance. Each feature plan MUST perform the Constitution Check before research and again
after design. Each pull request and each evidence freeze MUST document compliance or a
ratified exception. A quarterly review is required while experiments or production work
are active, plus a review before every dataset freeze, paper submission, or production
promotion.

**Version**: 1.0.1 | **Ratified**: 2026-07-21 | **Last Amended**: 2026-09-15
