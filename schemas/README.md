# RecruitSecBench dataset schemas

JSON Schema Draft 2020-12 contracts for the five datasets described in the
experimental roadmap. Each schema validates **one JSONL line**, not an entire
file-sized array.

## Files

| Dataset | Record schema | Primary key | Purpose |
|---|---|---|---|
| Domain | `domain.schema.json` | `record_id` | CVs, vacancies, and individual candidate responses |
| Benign | `benign.schema.json` | `case_id` | Legitimate tasks, permissions, utility oracles, and expected outcomes |
| Adversarial | `adversarial.schema.json` | `case_id` | Attacks, validity conditions, prohibited outcomes, and attack-success oracles |
| Deterministic | `deterministic.schema.json` | `fixture_id` | Tool calls, ID bindings, states, scopes, and canaries |
| Audit | `audit.schema.json` | `trace_id` | Raw repetitions, events, deterministic results, human labels, and S4 predictions |

`common.schema.json` contains shared definitions. `manifest.schema.json` defines
the version, hashes, partitions, privacy review, and upstream dependencies for
each frozen dataset artifact.

## Canonical ID mapping

The research vocabulary is stable even when application APIs use aliases:

| Benchmark field | SmartRH concept |
|---|---|
| `vacancy_id` | `HiringProcessOpening.id`, also called `vaga_id`, `job_opening_id`, or `openingId` |
| `application_id` | `Application.id`, also called `candidatura_id` |
| `candidate_id` | Anonymized logical candidate ID; it is not an email, CPF, or public user ID |
| `hiring_process_id` | `HiringProcess.id`, also called `processoSeletivoId` |

Aliases belong in adapter code and traces, not as duplicate canonical fields in
the datasets.

## Referential graph

```text
domain.record_id <--- benign.input_record_ids
       ^                      |
       |                      v
       +--- adversarial.input_record_ids
                   |
                   +-- benign_case_id ---> benign.case_id

deterministic.fixture_id <--- benign/adversarial.fixture_ids

benign/adversarial.case_id <--- audit.case_id
run_id + case_id + condition + repetition ---> one audit.trace_id
```

## Required semantic invariants

JSON Schema validates structure. The harness must additionally enforce these
cross-record invariants:

1. IDs are globally unique within their namespace. A `case_id` identifies the
   scenario; it never identifies an execution or repetition.
2. Every foreign reference resolves against the frozen upstream manifests.
3. An adversarial mutation should set `benign_case_id`. It may be absent only
   when no legitimate counterpart exists, such as an isolated invalid-state case.
4. `record_type` must agree with `content.kind`; `fixture_type` must agree with
   `fixture.kind`.
5. Scope ancestry is valid: vacancy belongs to hiring process, hiring process to
   project, application to vacancy, answer to application/questionnaire.
6. Event `sequence` values are unique and strictly increasing inside a trace.
7. `auditor_view.included_event_ids` all exist in `events`; human labels,
   deterministic outcomes, and auditor predictions never enter that view.
8. Provider/harness failures remain in `execution.status`. They are not silently
   converted into attack success, benign failure, SAFE, or BLOCK.
9. A final audit gold set has at least one independent `human_annotations` item;
   disagreements receive `adjudication` without overwriting original labels.
10. Canaries are synthetic markers, never real secrets. A canary hit is recorded
    at each observed stage: retrieval, context, tool, output, or trace.

## Hashing rule

Hash files as their exact UTF-8 bytes. For `content_sha256` on an object, serialize
JSON as UTF-8 with sorted keys, no insignificant whitespace, and no ASCII escaping
before applying SHA-256. Record the hashing implementation in the manifest notes.

## Privacy rule

Original CVs do not enter this structure. Domain rows contain synthetic or
authorized anonymized derivatives. Audit rows store minimized events, hashes,
IDs, and short sanitized evidence; `full_prompts_stored` and `full_cv_stored` are
fixed to `false` by the schema.

## Suggested artifact layout

```text
recruitsecbench/
  schemas/
  data/
    domain/{development,pilot,evaluation,holdout}.jsonl
    benign/{development,pilot,evaluation,holdout}.jsonl
    adversarial/{development,pilot,evaluation,holdout}.jsonl
    deterministic/{development,pilot,evaluation,holdout}.jsonl
    audit/{development,pilot,evaluation,holdout}.jsonl
  manifests/
    domain.manifest.json
    benign.manifest.json
    adversarial.manifest.json
    deterministic.manifest.json
    audit.manifest.json
```

The `examples/` directory contains one valid record for each requested dataset.
