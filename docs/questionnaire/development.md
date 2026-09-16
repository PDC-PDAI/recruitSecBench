# Arquitetura e desenvolvimento

🇧🇷 **Português** · [🇺🇸 English](development.en.md) · [Início](../../README.md)

## Ambiente e configuração

A distribuição Python `recruitsecbench` inclui os pacotes `recruitsecbench` e
`rscb_questionnaire`. Execute os comandos na raiz: um único `pyproject.toml`
declara dependências, comandos e testes; `uv.lock` fixa o ambiente da reprodução.

O perfil padrão e o corpus da bateria são incluídos na distribuição. A CLI
instalada funciona fora do checkout. `.env` e SQLite usam o diretório de execução
ou `QUESTIONNAIRE_HOME`. Os prompts remotos usam `recruitsecbench/questionnaire/`,
com namespace próprio para cada defesa.

O fluxo completo seleciona gerador e avaliador por `--defense` ou
`QUESTIONNAIRE_DEFENSE`. A API salva essa escolha no cenário e a usa nas avaliações
posteriores. Veja [defesas e bateria R1](defenses.md) para protocolos de comparação
e o mapa das implementações.

## Componentes

| Caminho em `rscb_questionnaire/` | Responsabilidade |
|---|---|
| `variants/`, `battery.py` | Baseline histórico, FIDES/CaMeL e bateria de geração |
| `agents/` | Modelos e adaptação por provider/papel |
| `prompts/` | Conteúdo local, templates e resolução Langfuse |
| `services/job_description/`, `services/coordinator_prompt/` | Preparação do cenário e comandos |
| `services/questionnaire/` | ReAct, tools e validação do questionário |
| `services/response/`, `services/submission/` | Casos sintéticos e validação das respostas |
| `services/evaluation/` | Avaliação `FORMULARIO` e oráculo determinístico |
| `services/scenario/` | Encadeamento e registros do benchmark |
| `services/agent_debug/`, `services/observability/` | Contrato de trajetória, checkpoints e tracing |
| `api/`, `repositories/` | API e persistência SQLite |
| `schemas/` | Contratos executáveis |
| `sync_prompts.py`, `profiles/security.yaml` | Recursos incluídos no pacote instalado |

## Alterar o experimento

Para uma categoria de resposta, atualize `schemas/response/schema.py`, os prompts
do gerador, o oráculo quando necessário e testes com casos benignos/adversariais.
Mudanças de limiar ou de interpretação de canários alteram o protocolo: registre
isso no método e separe os novos resultados dos anteriores.

Para providers, altere `agents/model.py` e verifique herança e overrides com os
testes por papel. Para contratos de API, mantenha a visão pública sem `weight`
e `rationale` e valide submissões antes de chamar o avaliador. Migrações SQLite
devem preservar os dados existentes e a idempotência da avaliação.

```bash
uv run ruff check .
uv run pytest -q
uv build
```

Os testes cobrem modelos substitutos, respostas adversariais, proveniência,
submissões, exportação e API. O CI executa as duas frentes na mesma instalação e suíte de testes.
Não há execução paga de LLM nem sincronização de prompts remotos durante testes.

Os registros históricos da importação ficam em
[`docs/provenance/`](../provenance/). Os caminhos e hashes nesses JSONs descrevem
a importação original, anterior à organização em `src/` e `tests/questionnaire/`;
não são manifestos do estado atual. Os prompts, corpus e revisões históricas das
defesas foram preservados nesta reorganização.
