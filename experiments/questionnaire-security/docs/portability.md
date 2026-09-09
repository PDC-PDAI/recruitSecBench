# Portabilidade e desenvolvimento

🇧🇷 **Português** · [🇺🇸 English](portability.en.md) · [Início](../README.md)

O fluxo completo aceita `baseline`, `baseline_r1`, `fides` e `camel` no gerador
e no avaliador. Veja [defesas e bateria histórica](defenses.md) para as revisões
de origem, diferenças entre serviços e o protocolo exclusivo de geração.

## Fronteira do projeto

O experimento é uma distribuição Python própria, `recruitsecbench-questionnaire`,
com pacote `rscb_questionnaire` e comando `rscb-questionnaire`. Seu `pyproject.toml`
e `uv.lock` preservam as dependências do código de origem. A raiz do RecruitSecBench
continua com o pacote `recruitsecbench`, CLI `rscb` e ambiente anterior.

Não há import de `src`, symlink, dependência Git ou caminho para Scenario Emulator.
O perfil padrão é incluído na distribuição; a CLI instalada funciona fora do
checkout. `.env` e SQLite ficam no diretório de execução ou em `QUESTIONNAIRE_HOME`.

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

## Adaptações da origem

- Namespace Python `src` → `rscb_questionnaire`, incluindo strings de import dinâmico.
- CLI com perfil de segurança padrão; comandos de campanhas de falhas não são portados.
- Prompts remotos usam `recruitsecbench/questionnaire/`; o conteúdo experimental é preservado.
- Proveniência e nomes de serviço identificam o experimento do RecruitSecBench.
- Configuração e banco isolados do projeto pai; sync de prompts incluído no wheel.
- Testes da cadeia de segurança portados; fixture de outro perfil serve apenas à validação de fronteira.

O runner de falhas, as campanhas de 100/220/1.100 casos e os scripts de controles
v2 permanecem no Scenario Emulator. Tipos de falha e exportadores AgentDebug
continuam presentes porque a segurança também os usa para anotar suas trajetórias.
O antigo código de CVs não foi reescrito nem seus contratos foram convertidos.

[`PORTABILITY.json`](../PORTABILITY.json) registra commit de origem e SHA-256 dos
arquivos de origem e destino portados. Ao evoluir o código, use esse registro como
referência da portabilidade inicial, não como mecanismo automático de sincronização.

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
submissões, exportação e API. O CI executa este projeto em um job próprio.
Não há execução paga de LLM nem sincronização de prompts remotos durante testes.
