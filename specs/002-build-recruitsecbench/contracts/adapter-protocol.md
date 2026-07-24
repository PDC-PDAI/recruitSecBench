# Adapter Protocol

## Purpose

Adapters translate between canonical RecruitSecBench entities and the frozen SmartRH/Agno
interfaces. They never make authorization decisions and never duplicate aliases in
canonical datasets.

## Required interface

```python
class ApplicationAdapter(Protocol):
    async def doctor(self) -> AdapterHealth: ...
    async def reset(self, fixture_manifest: str) -> EnvironmentSnapshot: ...
    async def run(self, request: AdapterRequest) -> AdapterResult: ...
    async def snapshot(self) -> EnvironmentSnapshot: ...
    async def close(self) -> None: ...
```

`AdapterRequest` contains run ID, case ID, actor, authorization scope, canonical
operation, canonical arguments, condition, seed, timeout, and idempotency key.

`AdapterResult` contains normalized output, sanitized events, policy decisions, tool
calls, committed side effects, state diff, operational status, timings, token/cost
metadata, and adapter version.

## Canonical alias map

| Canonical | SmartRH/Agno aliases |
|---|---|
| `vacancy_id` | `HiringProcessOpening.id`, `openingId`, `vaga_id`, `job_opening_id`, `jobOpening_id` |
| `application_id` | `Application.id`, `candidaturaId`, `candidatura_id` |
| `hiring_process_id` | `HiringProcess.id`, `processoSeletivoId`, `hiringProcessId` |
| `questionnaire_id` | `Questionnaire.id`, `questionnaireId` |
| `question_id` | `Question.id`, `questionId` |

Normalization is explicit, one-way, logged by alias name and hash, and rejected when two
aliases resolve to conflicting canonical IDs.

## Execution adapters

### SimulatorAdapter

Uses the custom AgentDojo environment and in-memory canonical entities. Reset is a pure
load of the fixture manifest. This is the authoritative environment for the full matrix.

### SmartRHAdapter

Uses the isolated Compose stack and existing Platform/MCP/Agno contracts. It:

1. verifies repository commits and health endpoints;
2. loads only synthetic fixtures into an isolated database and Qdrant collection;
3. invokes API or MCP according to the case operation;
4. waits for bounded asynchronous completion where the real flow is asynchronous;
5. snapshots database, object, queue, and RAG state;
6. sanitizes output before returning it to the benchmark.

It must not call the web UI, production hostnames, Terraform, or shared volumes.

## ToolGateway contract

```python
class ToolGateway(Protocol):
    async def call(
        self,
        actor: ActorContext,
        scope: AuthorizationScope,
        stage: str,
        tool_name: str,
        arguments: dict[str, object],
        idempotency_key: str,
    ) -> GatewayResult: ...
```

Evaluation order is fixed:

1. authenticate actor;
2. resolve canonical aliases;
3. validate resource existence and ancestry;
4. enforce stage allowlist and operation permission;
5. validate input schema and bounds;
6. enforce state transition and round token;
7. enforce CaMeL capability, when enabled;
8. enforce FIDES flow policy, when enabled;
9. claim idempotency key;
10. call the underlying tool;
11. validate result and record side effects.

A denial stops before step 9 and has zero committed effects.

## Stable decisions and reason codes

Decisions: `ALLOW`, `DENY`, `HUMAN_REVIEW`, `ERROR`.

Minimum reason codes:

- `ACTOR_UNAUTHENTICATED`
- `ROLE_NOT_ALLOWED`
- `TOOL_NOT_ALLOWED`
- `RESOURCE_NOT_FOUND`
- `ID_ALIAS_CONFLICT`
- `ID_BINDING_INVALID`
- `CROSS_SCOPE_ACCESS`
- `ARGUMENT_SCHEMA_INVALID`
- `STATE_TRANSITION_INVALID`
- `ROUND_TOKEN_STALE`
- `DUPLICATE_EFFECT`
- `CAPABILITY_MISSING`
- `INTEGRITY_FLOW_BLOCKED`
- `CONFIDENTIALITY_FLOW_BLOCKED`
- `HUMAN_REVIEW_REQUIRED`
- `PROVIDER_ERROR`
- `HARNESS_ERROR`

## CaMeL adaptation boundary

Untrusted values become opaque variables. A tool-free quarantined model may transform
those values, but the result remains untrusted. The planner emits a typed program over
variable references and capabilities. The interpreter validates the program and resolves
only capabilities issued by the gateway. Raw untrusted bytes never become authority.

## FIDES adaptation boundary

Every content item has:

- integrity: `TRUSTED | UNTRUSTED`;
- confidentiality: `PUBLIC | INTERNAL | RESTRICTED | IDENTITY_SCOPED`;
- provenance and scope labels.

Labels propagate using the most restrictive join. Tool metadata identifies sources,
transformers, and sinks. A sink call is allowed only when the current label satisfies its
policy. Quarantined transformations do not raise integrity.

## Trace boundary

Adapters may emit only the event contract in `trace-event.schema.json`. Large text is
replaced by length, content hash, data class, and an optional short sanitized excerpt.
Original CVs, real derivatives, PII, credentials, full prompts, deterministic gold, and
human labels are forbidden.

## Compatibility rule

Any changed Platform, Agno, AgentDojo, tool, prompt, or adapter contract requires a new
adapter version and run manifest. An adapter may fail closed with
`ADAPTER_CONTRACT_MISMATCH`; it may not guess a replacement field or state.
