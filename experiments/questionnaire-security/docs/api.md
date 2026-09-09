# API de questionários e submissões

🇧🇷 **Português** · [🇺🇸 English](api.en.md) · [Início](../README.md)

## Iniciar

```bash
uv run rscb-questionnaire serve --host 127.0.0.1 --port 8000
```

Swagger em `/docs`, ReDoc em `/redoc` e contrato OpenAPI em `/openapi.json`.
A API não possui autenticação própria. O exemplo usa interface local.
`API_CORS_ORIGINS` configura origens CORS; o SQLite usa
`API_DATABASE_PATH` ou `data/questionnaire-security.db` no diretório do experimento.

## Fluxo manual

Crie um cenário, consulte seus questionários e substitua `SCENARIO_ID`,
`QUESTIONNAIRE_ID` e `SUBMISSION_ID` pelos identificadores devolvidos. Crie
`answers.json` com **todas as respostas obrigatórias** do questionário; o JSON
abaixo ilustra a estrutura e precisa ser completado para o formulário gerado.
Os números das perguntas começam em 1. Gerar cenários e avaliar submissões chama LLMs.

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

A visão pública omite `weight` e `rationale`; o payload de avaliação inclui esses
campos. Submissões são validadas antes de avaliar. Uma nova chamada a `evaluate`
reutiliza a avaliação persistida para a mesma submissão. O payload de handoff é
um contrato autocontido para integração; obter esse payload não executa um avaliador externo.

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

## Benchmarks e defaults

A API preserva os defaults históricos do contrato HTTP: três comandos benignos,
três maliciosos, uma resposta benigna e uma maliciosa por formulário. Ela não lê o
YAML da CLI. Envie as quatro contagens explicitamente para comparar execuções.
Para reproduzir o perfil da CLI, use `1`, `3`, `1`, `2`, respectivamente.

Submissões manuais sem caso sintético têm `benchmark_applicable=false`: não há
rótulo de intenção nem limiar de nota, apenas as verificações aplicáveis de
proveniência e canário de sistema. Veja o [método](methodology.md).
