# Baselines, FIDES, CaMeL e bateria R1

🇧🇷 **Português** · [🇺🇸 English](defenses.en.md) · [Início](../README.md)

## Variantes experimentais

FIDES e CaMeL implementam mecanismos de defesa para comparar como o gerador de
questionários e o avaliador de respostas lidam com conteúdo adversarial. Cada
variante seleciona um gerador e um avaliador sob o mesmo contrato de cenário.

| `--defense` | Papel no experimento | Gerador e avaliador |
|---|---|---|
| `baseline` | Baseline padrão do fluxo completo | Serviços padrão de geração e avaliação |
| `baseline_r1` | Referência da bateria R1 | Serviços de geração e avaliação da versão R1 |
| `fides` | Defesa com rótulos de fluxo de informação | Referências opacas, rótulos de integridade/confidencialidade, monitor de permissões e LLM em quarentena |
| `camel` | Defesa com separação entre controle e dados | Processamento em quarentena e políticas de proveniência nas saídas |

São implementações experimentais do projeto. Os testes verificam seu comportamento
local; não demonstram eficácia contra modelos reais nem equivalência integral às
implementações de referência dos trabalhos FIDES/CaMeL.

## Onde desenvolver

Todos os caminhos abaixo são relativos a `rscb_questionnaire/`:

| Variante | Gerador | Avaliador | Políticas e mecanismos |
|---|---|---|---|
| Baseline atual | [`services/questionnaire/service.py`](../rscb_questionnaire/services/questionnaire/service.py) | [`services/evaluation/service.py`](../rscb_questionnaire/services/evaluation/service.py) | Validações e oráculo comuns |
| Baseline R1 | [`variants/baseline_r1/questionnaire.py`](../rscb_questionnaire/variants/baseline_r1/questionnaire.py) | [`variants/baseline_r1/evaluation.py`](../rscb_questionnaire/variants/baseline_r1/evaluation.py) | Implementação R1 |
| FIDES | [`variants/fides/questionnaire.py`](../rscb_questionnaire/variants/fides/questionnaire.py) | [`variants/fides/evaluation.py`](../rscb_questionnaire/variants/fides/evaluation.py) | [`variants/fides/security/fides.py`](../rscb_questionnaire/variants/fides/security/fides.py) |
| CaMeL | [`variants/camel/questionnaire.py`](../rscb_questionnaire/variants/camel/questionnaire.py) | [`variants/camel/evaluation.py`](../rscb_questionnaire/variants/camel/evaluation.py) | [`variants/camel/security/`](../rscb_questionnaire/variants/camel/security/) |

Cada variante mantém seus prompts locais. A preparação de vagas/comandos, geração
de respostas, schemas, oráculo, persistência e integração com providers usam o
runtime comum. A seleção instancia os dois serviços, sem trocar branches ou
modificar classes globais. Os testes de FIDES/CaMeL cobrem os mecanismos e seu uso pelos dois serviços.

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

## Bateria R1 de geração

O comando [`rscb-questionnaire-battery`](../rscb_questionnaire/battery.py) executa
a campanha de geração. O [corpus YAML](../configs/questionnaire_battery.yaml)
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

## Comparação reproduzível

Fixe o commit do RecruitSecBench, lockfile, corpus, prompts resolvidos e
configuração do provider em cada campanha. As variantes usam runtime comum;
alterações de provider, retries ou prompts exigem registrar uma nova configuração.

Compare `baseline_r1`, FIDES e CaMeL com o mesmo corpus, modelo, parâmetros e número
de repetições. O fluxo completo gera novos comandos e respostas por LLM e não
constitui automaticamente uma comparação pareada. Separe protocolos de geração
e avaliação, reporte cobertura/recusas/erros e use o [método](methodology.md) para
interpretar o oráculo. O repositório fornece código e configurações. Reanalisar uma campanha concluída
exige seus artefatos salvos; uma nova execução com LLM pode produzir outras saídas.
