# Questionnaire and submission API

[🇧🇷 Português](api.md) · 🇺🇸 **English** · [Home](../README.en.md)

The full pipeline supports `baseline`, `baseline_r1`, `fides` and `camel` for
both generation and evaluation. See [defenses and R1 battery](defenses.en.md)
for experimental variants, service differences and the generation-only protocol.

## Start

```bash
uv run rscb-questionnaire serve --host 127.0.0.1 --port 8000
```

Swagger is at `/docs`, ReDoc at `/redoc`, and OpenAPI at `/openapi.json`.
The API has no built-in authentication. This example binds locally.
`API_CORS_ORIGINS` configures allowed origins; SQLite uses `API_DATABASE_PATH`
or `data/questionnaire-security.db` in the experiment directory.

## Manual flow

Create a scenario, list its questionnaires, and replace `SCENARIO_ID`,
`QUESTIONNAIRE_ID`, and `SUBMISSION_ID` with returned identifiers. Create
`answers.json` with **all required answers**; the JSON below illustrates the
structure and must be completed for the generated form. Question numbers start
at 1. Scenario generation and submission evaluation call LLMs.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scenarios \
  -H 'Content-Type: application/json' \
  -d '{"brief":"Vaga backend Python e FastAPI", "benign_count":1,
       "malicious_count":0, "benign_response_count":0, "malicious_response_count":0}'

curl http://127.0.0.1:8000/api/v1/scenarios/SCENARIO_ID/questionnaires
curl http://127.0.0.1:8000/api/v1/questionnaires/QUESTIONNAIRE_ID

curl -X POST http://127.0.0.1:8000/api/v1/questionnaires/QUESTIONNAIRE_ID/submissions \
  -H 'Content-Type: application/json' \
  --data-binary @answers.json

curl -X POST http://127.0.0.1:8000/api/v1/submissions/SUBMISSION_ID/evaluate
curl http://127.0.0.1:8000/api/v1/submissions/SUBMISSION_ID/evaluation
```

```json
{
  "respondent_reference": "candidate-pseudo-42",
  "answers": [
    {"question_number": 1, "text": "Resposta à primeira pergunta / Answer to question one"}
  ]
}
```

Public views omit `weight` and `rationale`; evaluation payloads include them.
Submissions are validated before evaluation. Repeated `evaluate` calls reuse the
persisted evaluation for that submission. The handoff payload is a self-contained
integration contract; retrieving it does not execute an external evaluator.

## Endpoints

| Método / Method | Endpoint | Uso / Purpose |
|---|---|---|
| `POST` | `/api/v1/scenarios` | Geração / Generation |
| `GET` | `/api/v1/scenarios` | Listagem / Listing |
| `GET` | `/api/v1/scenarios/{id}` | Cenário completo / Complete scenario |
| `GET` | `/api/v1/scenarios/{id}/questionnaires` | Formulários válidos / Valid questionnaires |
| `GET` | `/api/v1/questionnaires/{id}` | Visão pública / Public view |
| `POST` | `/api/v1/questionnaires/{id}/submissions` | Submissão / Submission |
| `POST` | `/api/v1/submissions/{id}/evaluate` | Avaliação idempotente / Idempotent evaluation |
| `GET` | `/api/v1/submissions/{id}/evaluation` | Avaliação salva / Saved evaluation |
| `GET` | `/api/v1/scenarios/{id}/evaluations` | Avaliações do cenário / Scenario evaluations |
| `GET` | `/api/v1/submissions/{id}/evaluation-payload` | Handoff para avaliador externo / External evaluator handoff |
| `GET` | `/api/v1/scenarios/{id}/benchmark.jsonl` | Benchmark JSONL |
| `GET` | `/api/v1/scenarios/{id}/agent-debug.jsonl` | Trajetórias / Trajectories |

## Benchmarks and defaults

The API retains historical HTTP defaults: three benign commands, three malicious
commands, one benign and one malicious answer case per form. It does not load
the CLI YAML. Send all four counts explicitly for comparable runs. To match the
CLI profile, use `1`, `3`, `1`, `2`, respectively.

Manual submissions without a synthetic case have `benchmark_applicable=false`:
no intent label or score threshold, only applicable provenance and system-canary
checks. See the [methodology](methodology.en.md).
