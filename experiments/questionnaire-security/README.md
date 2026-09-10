# Segurança de questionários

🇧🇷 **Português** · [🇺🇸 English](README.en.md) · [RecruitSecBench](../../README.md)

Guia de execução do experimento de segurança de questionários: geração de vagas e
questionários, comandos adversariais, respostas sintéticas e avaliação da dimensão
`FORMULARIO`. Veja a [visão do experimento e as figuras do artigo](../../README.md#visão-do-experimento).

## Baseline, FIDES e CaMeL

As variantes incluem **gerador e avaliador**. Use `run --defense fides` ou
`run --defense camel`; `baseline` é o padrão do fluxo completo
e `baseline_r1` é a referência da bateria R1.

A bateria de 380 casos por repetição também está incluída:
`uv run rscb-questionnaire-battery --defense fides --dry-run`.
Ela testa somente geração; o comando `run` executa o fluxo com avaliador.
Veja [variantes, implementações e comandos](docs/defenses.md).

## Instalação e configuração

Execute os comandos deste guia em `experiments/questionnaire-security/`.

```bash
uv sync --locked
cp .env.example .env
uv run rscb-questionnaire --help
uv run rscb-questionnaire validate-profile configs/fronts/security.yaml
```

Edite `.env` para configurar o provider:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5-mini
LANGFUSE_TRACING_ENABLED=false
```

Também são aceitos `openai_responses`, `openai_like`, `ollama` e `ceia`. O
[.env.example](.env.example) mostra os parâmetros. Para comparar modelos por papel,
use `RESPONSE_GENERATOR_LLM_PROVIDER`/`RESPONSE_GENERATOR_MODEL` e
`EVALUATOR_LLM_PROVIDER`/`EVALUATOR_MODEL`; campos ausentes herdam a configuração global.

O `.env` é lido do diretório de trabalho, sem procurar o projeto pai.
`QUESTIONNAIRE_HOME` permite escolher outro diretório para `.env` e o banco padrão.
Caminhos explícitos no YAML e `API_DATABASE_PATH` relativos continuam relativos
ao diretório de trabalho. O banco padrão é `data/questionnaire-security.db`.

## Executar

Smoke com uma resposta benigna, usando LLM:

```bash
uv run rscb-questionnaire run \
  --brief "Vaga sênior de backend Python, FastAPI e PostgreSQL" \
  --benign 1 --malicious 0 \
  --benign-responses 1 --malicious-responses 0
```

Experimento adversarial padrão:

```bash
uv run rscb-questionnaire run \
  --profile configs/fronts/security.yaml \
  --brief "Vaga sênior de backend Python, FastAPI e PostgreSQL"
```

| Configuração padrão | Quantidade |
|---|---:|
| Comandos benignos | 1 |
| Comandos maliciosos | 3 |
| Respostas benignas por questionário produzido | 1 |
| Respostas maliciosas por questionário produzido | 2 |

Uma resposta é um conjunto de respostas às perguntas, não uma única pergunta.
O avaliador roda para cada caso gerado. Questionários recusados ou com falha não
seguem para respostas/avaliação. `--brief-file briefing.txt` substitui `--brief`.
Flags explícitas sobrescrevem o YAML. Para testar apenas a geração, use
`--benign-responses 0 --malicious-responses 0 --no-questionnaire-evaluator`.

## Guardar uma execução

Os caminhos padrão são reutilizados. Escolha caminhos novos para preservar cada
execução e arquive junto o perfil, o briefing, o commit, o lockfile e os modelos:

```bash
uv run rscb-questionnaire run \
  --brief-file briefing.txt \
  --output outputs/run-001/scenario.json \
  --jsonl outputs/run-001/benchmark.jsonl \
  --agent-debug-jsonl outputs/run-001/agent-debug.jsonl \
  --trajectories-dir outputs/run-001/trajectories
```

| Artefato | Conteúdo |
|---|---|
| `scenario.json` | Vaga, comandos, questionários, casos de resposta, avaliações e registros do benchmark |
| `benchmark.jsonl` | Um `BenchmarkRecord` por trajetória: geração, lote de respostas ou avaliação |
| `agent-debug.jsonl` | Trajetórias no contrato AgentDebug; formato de intercâmbio preservado |
| `trajectories/` | As mesmas trajetórias em arquivos individuais |

Os schemas executáveis ficam em `rscb_questionnaire/schemas/`. A CLI pode terminar
com código zero mesmo com falhas no benchmark; avalie os registros e os oráculos.
Não some todos os tipos de trajetória em uma única taxa de sucesso.

## API e observabilidade

```bash
uv run rscb-questionnaire serve --host 127.0.0.1 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`. Veja o [guia da API](docs/api.md) para
questionários públicos, submissões, avaliação idempotente e exportação.

Langfuse é opcional. Use um projeto dedicado, configure as três credenciais
`LANGFUSE_*` e ative `LANGFUSE_TRACING_ENABLED=true`. Os prompts usam o namespace
`recruitsecbench/questionnaire/`, com namespace próprio para cada defesa.

```bash
uv run rscb-questionnaire sync-prompts
uv run rscb-questionnaire export-trace --trace-id TRACE_ID --output outputs/trace.json
```

`LANGFUSE_SYNC_LABEL` define o destino do sync e `LANGFUSE_PROMPT_LABEL` o label
lido no runtime. Configure ambos como `dev` para desenvolvimento; `latest` é
rejeitado. Sem Langfuse, o conteúdo dos prompts locais continua disponível.

## Desenvolver e verificar

```bash
uv run ruff check .
uv run pytest -q
uv build
```

| Guia | Português | English |
|---|---|---|
| FIDES, CaMeL e bateria R1 | [Defesas](docs/defenses.md) | [Defenses](docs/defenses.en.md) |
| Método, oráculos e reprodução | [Método](docs/methodology.md) | [Methodology](docs/methodology.en.md) |
| Arquitetura e desenvolvimento | [Desenvolvimento](docs/development.md) | [Development](docs/development.en.md) |
| API e submissões | [API](docs/api.md) | [API](docs/api.en.md) |

Os testes usam modelos substitutos e tracing desabilitado. Eles verificam a
implementação; não são resultados empíricos de robustez contra modelos reais.
