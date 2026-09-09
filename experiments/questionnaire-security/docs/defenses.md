# FIDES, CaMeL e bateria histórica

🇧🇷 **Português** · [🇺🇸 English](defenses.en.md) · [Início](../README.md)

## Por que fazem parte

FIDES e CaMeL são as variantes de defesa implementadas neste projeto para comparar
como o gerador de questionários e o avaliador de respostas lidam com conteúdo
adversarial. A primeira portabilidade trouxe apenas a branch de trabalho vigente;
estas implementações estavam em outras branches do Scenario Emulator.

| `--defense` | Origem no Scenario Emulator | Gerador e avaliador |
|---|---|---|
| `baseline` | `8fd93c0` — portabilidade inicial | Implementação corrente na separação dos repos |
| `baseline_r1` | `bateria-testes-r1` · `acd083a` | Baseline histórico da bateria, preservado como variante própria |
| `fides` | `feat/fides` · `3aae97d` | Referências opacas, rótulos de integridade/confidencialidade, monitor de permissões e LLM em quarentena |
| `camel` | `feat/camel` · `804bece` | Separação entre controle e dados, processamento em quarentena e políticas de proveniência nas saídas |

São implementações experimentais do projeto. Os testes verificam seu comportamento
local; não demonstram eficácia contra modelos reais nem equivalência integral às
implementações de referência dos trabalhos FIDES/CaMeL.

## Onde desenvolver

Todos os caminhos abaixo são relativos a `rscb_questionnaire/`:

| Variante | Gerador | Avaliador | Políticas e mecanismos |
|---|---|---|---|
| Baseline atual | [`services/questionnaire/service.py`](../rscb_questionnaire/services/questionnaire/service.py) | [`services/evaluation/service.py`](../rscb_questionnaire/services/evaluation/service.py) | Validações e oráculo comuns |
| Baseline R1 | [`variants/baseline_r1/questionnaire.py`](../rscb_questionnaire/variants/baseline_r1/questionnaire.py) | [`variants/baseline_r1/evaluation.py`](../rscb_questionnaire/variants/baseline_r1/evaluation.py) | Implementação histórica |
| FIDES | [`variants/fides/questionnaire.py`](../rscb_questionnaire/variants/fides/questionnaire.py) | [`variants/fides/evaluation.py`](../rscb_questionnaire/variants/fides/evaluation.py) | [`variants/fides/security/fides.py`](../rscb_questionnaire/variants/fides/security/fides.py) |
| CaMeL | [`variants/camel/questionnaire.py`](../rscb_questionnaire/variants/camel/questionnaire.py) | [`variants/camel/evaluation.py`](../rscb_questionnaire/variants/camel/evaluation.py) | [`variants/camel/security/`](../rscb_questionnaire/variants/camel/security/) |

Cada variante mantém seus prompts locais. A preparação de vagas/comandos, geração
de respostas, schemas, oráculo, persistência e integração com providers usam o
runtime comum. A seleção instancia os dois serviços, sem trocar branches ou
modificar classes globais. Testes de FIDES/CaMeL foram portados junto do código.

## Fluxo completo com avaliador

No diretório `experiments/questionnaire-security/`, após configurar `.env`:

```bash
uv run rscb-questionnaire run --defense fides \
  --brief "Vaga backend Python e FastAPI" \
  --output outputs/fides/run-001/scenario.json \
  --jsonl outputs/fides/run-001/benchmark.jsonl \
  --agent-debug-jsonl outputs/fides/run-001/agent-debug.jsonl \
  --trajectories-dir outputs/fides/run-001/trajectories
```

Troque `fides` por `camel`, `baseline_r1` ou `baseline`, usando outro diretório.
O perfil padrão gera comandos, questionários, respostas e avaliações. Uma recusa
na geração impede as etapas posteriores daquele caso. `--defense` prevalece sobre
`QUESTIONNAIRE_DEFENSE`, cujo padrão é `baseline`. O campo `defense` fica salvo no
cenário; os registros do benchmark incluem variante e commit original.

Na API, envie `"defense": "fides"` ao criar o cenário. Avaliações manuais usam a
variante salva no cenário, inclusive após reiniciar o servidor com outra
configuração. Cenários antigos sem esse campo são interpretados como `baseline`.

Com Langfuse, sincronize primeiro os prompts comuns e depois os da variante:

```bash
uv run rscb-questionnaire sync-prompts --defense baseline
uv run rscb-questionnaire sync-prompts --defense fides
uv run rscb-questionnaire sync-prompts --defense camel
```

Os serviços específicos usam `recruitsecbench/questionnaire/<variante>/`; os
serviços comuns continuam em `recruitsecbench/questionnaire/`. Sem Langfuse,
os prompts locais são usados. Para reprodução, arquive o conteúdo efetivamente
resolvido e as versões remotas, quando houver.

## Bateria original de geração

O comando [`rscb-questionnaire-battery`](../rscb_questionnaire/battery.py) porta
`scripts/run_questionnaire_battery.py`. O [corpus YAML](../configs/questionnaire_battery.yaml)
contém **5 vagas × (15 temas × 5 níveis + 1 controle) = 380 gerações por repetição**:
375 ataques e 5 controles. O YAML também é incluído no pacote instalado.

Esta bateria **não gera respostas, não chama o avaliador e não classifica os
resultados**. `status` registra o resultado operacional do gerador; não é uma
classificação posterior de segurança. O manifesto mantém
`evaluation_enabled=false` e `classification_enabled=false`.

```bash
# Valida corpus e prepara manifesto/SQLite, sem chamar LLM
uv run rscb-questionnaire-battery --defense baseline_r1 --dry-run
uv run rscb-questionnaire-battery --defense fides --dry-run
uv run rscb-questionnaire-battery --defense camel --dry-run

# Executa no máximo um item pendente, com o modelo configurado
uv run rscb-questionnaire-battery --defense fides --limit 1

# Continua a mesma campanha; sem --limit, executa todos os itens pendentes
uv run rscb-questionnaire-battery --defense fides --concurrency 3
```

O padrão desta CLI é `baseline_r1`, independentemente de `QUESTIONNAIRE_DEFENSE`,
para identificar o baseline da bateria. As saídas padrão são
`outputs/questionnaire-battery-<variante>/`. `--output-dir`, `--config` e
`--repetitions` permitem campanhas separadas. Cada diretório contém manifesto,
`generations.jsonl`, JSONs individuais, `questionnaire_battery.sqlite3`, resumo e
dicionário de dados. O formato histórico conserva questionário, status, IDs de
trajetória/trace e duração; não contém a exportação AgentDebug completa.

A retomada verifica defesa, revisão de origem, provider/modelo, corpus e
repetições antes de reutilizar o diretório. Configuração incompatível exige outro
diretório. Todos os itens já registrados, inclusive `runtime_error`, são considerados
concluídos na retomada. Use outra campanha para repetir esses casos. Arquive também commit atual, lockfile,
configuração completa do provider e prompts; o manifesto não captura todos os
parâmetros externos de execução.

## Fidelidade e comparação

[`DEFENSE_PORTABILITY.json`](../DEFENSE_PORTABILITY.json) registra commits e hashes
de origem/destino desta extensão. [`PORTABILITY.json`](../PORTABILITY.json)
continua como fotografia da portabilidade inicial. O port adapta imports,
namespaces de prompts, seleção de serviços e proveniência. O runtime compartilhado
inclui melhorias posteriores de retries, OpenRouter e observabilidade; portanto,
não é um checkout byte a byte de cada branch histórica.

Compare `baseline_r1`, FIDES e CaMeL com o mesmo corpus, modelo, parâmetros e número
de repetições. O fluxo completo gera novos comandos e respostas por LLM e não
constitui automaticamente uma comparação pareada. Separe protocolos de geração
e avaliação, reporte cobertura/recusas/erros e use o [método](methodology.md) para
interpretar o oráculo. Nenhum resultado histórico, credencial ou execução paga foi
transferido ou produzido por esta portabilidade.
