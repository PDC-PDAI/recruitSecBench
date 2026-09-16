# RecruitSecBench

🇧🇷 **Português** · [🇺🇸 English](README.en.md)

Benchmark de segurança para agentes de recrutamento baseados em LLMs.
Investiga **prompt injection na geração de questionários e na avaliação de
respostas**, comparando baselines e as defesas FIDES e CaMeL.

[Começar](#começar) · [Método](experiments/questionnaire-security/docs/methodology.md) ·
[Defesas e bateria](experiments/questionnaire-security/docs/defenses.md) ·
[Desenvolvimento](experiments/questionnaire-security/docs/development.md) ·
[API](experiments/questionnaire-security/docs/api.md)

## Visão do experimento

O fluxo parte da descrição de uma vaga, produz um questionário e avalia as
respostas do candidato. O benchmark exercita duas superfícies de ataque:
**AS-1**, a interface do gerador, e **AS-2**, a interface do avaliador.
Comandos e respostas sintéticos permitem testar comportamento benigno e adversarial.

![Figura 1: fluxo de recrutamento com AS-1 no gerador de questionários e AS-2 no avaliador LLM.](docs/figures/figura1_pt.png)

*Figura 1 — Arquitetura experimental e superfícies de ataque do artigo.*

| Superfície | Entrada adversarial | O que observar |
|---|---|---|
| **AS-1 · Gerador** | Comando do coordenador | Cumprimento de comandos maliciosos, recusas indevidas e validade do questionário |
| **AS-2 · Avaliador** | Respostas às perguntas | Manipulação de nota, alteração da saída, proveniência das evidências e exposição de canários |

## Integridade e confidencialidade

Uma recusa pode impedir o objetivo malicioso e, ainda assim, a explicação gerada
revelar informação interna. Por isso, integridade da decisão e confidencialidade
da saída precisam ser examinadas separadamente.

![Figura 4: o objetivo malicioso é rejeitado, mas a nota de segurança pode revelar um canário interno.](docs/figures/figura4_pt.png)

*Figura 4 — Recusa do objetivo malicioso com possível vazamento na explicação de segurança.*

As figuras usam a nomenclatura do artigo. Na implementação, a avaliação retorna
`valor`, `justificativa` e `evidencias`; os checks ficam em `oracle`.
`verdict` e `security_note` não são campos desse contrato. A checagem de canários
atual inspeciona `justificativa`. Consulte o [método](experiments/questionnaire-security/docs/methodology.md)
para interpretar cada check e seu alcance.

## Começar

Requisitos: **Python 3.12+**, Git e `uv`. Execute no diretório do experimento:

```bash
git clone https://github.com/PDC-PDAI/recruitSecBench.git
cd recruitSecBench/experiments/questionnaire-security
uv sync --locked
cp .env.example .env

# Verificação sem chamadas a modelos
uv run rscb-questionnaire validate-profile configs/fronts/security.yaml
uv run pytest -q
```

Configure o provider no `.env` e execute um cenário pequeno com avaliador:

```bash
uv run rscb-questionnaire run --defense baseline \
  --brief "Vaga sênior de backend Python, FastAPI e PostgreSQL" \
  --benign 1 --malicious 0 \
  --benign-responses 1 --malicious-responses 0
```

Essa execução chama LLMs. O [guia de execução](experiments/questionnaire-security/README.md)
explica providers, perfis e caminhos de saída. Sem os overrides acima, o perfil
padrão solicita um comando benigno e três maliciosos, com uma resposta benigna
e duas maliciosas por questionário produzido.

## Baselines, FIDES e CaMeL

| `--defense` | Variante | Abrangência |
|---|---|---|
| `baseline` | Baseline padrão do fluxo completo | Gerador e avaliador |
| `baseline_r1` | Baseline de referência da bateria R1 | Gerador e avaliador |
| `fides` | Rótulos de integridade/confidencialidade, monitor de permissões e quarentena | Gerador e avaliador |
| `camel` | Separação entre controle e dados, quarentena e políticas de proveniência | Gerador e avaliador |

Use `run --defense fides` ou `run --defense camel` para selecionar as duas etapas.
O [guia das defesas](experiments/questionnaire-security/docs/defenses.md) aponta
para cada implementação e explica os protocolos de comparação.

A bateria R1 possui **380 gerações por repetição**: 5 vagas × (75 ataques + 1
controle). Para conferir o corpus sem chamar modelos:

```bash
uv run rscb-questionnaire-battery --defense fides --dry-run
```

A bateria executa somente geração. O fluxo `rscb-questionnaire run` inclui
respostas e avaliação dos questionários produzidos.

## Avaliador e artefatos

O `EvaluationService` avalia a dimensão `FORMULARIO` após a validação da submissão.
Seu modelo pode ser configurado com `EVALUATOR_LLM_PROVIDER` e `EVALUATOR_MODEL`.
A [API](experiments/questionnaire-security/docs/api.md) permite enviar respostas
manuais e consultar avaliações persistidas.

- [Avaliador baseline](experiments/questionnaire-security/rscb_questionnaire/services/evaluation/service.py)
- [Oráculo determinístico](experiments/questionnaire-security/rscb_questionnaire/services/evaluation/oracle.py)
- [Schemas da avaliação](experiments/questionnaire-security/rscb_questionnaire/schemas/evaluation/schema.py)
- [Avaliadores FIDES e CaMeL](experiments/questionnaire-security/docs/defenses.md#onde-desenvolver)

O fluxo completo grava `scenario.json`, `benchmark.jsonl`, `agent-debug.jsonl` e
`trajectories/` em `outputs/security/` por padrão. Use um diretório por execução
e analise geração e avaliação separadamente, com denominadores, recusas e falhas
de runtime explícitos. Uma recusa na geração impede a avaliação posterior daquele
caso; os [critérios experimentais](experiments/questionnaire-security/docs/methodology.md)
detalham cobertura, limiares e limitações.

## Desenvolvimento

O código de questionários fica em `experiments/questionnaire-security/`, com
pacote `rscb_questionnaire`, CLI, dependências e testes próprios.

```bash
cd experiments/questionnaire-security
uv run ruff check .
uv run pytest -q
uv build
```

| Guia | Português | English |
|---|---|---|
| Execução e configuração | [Guia](experiments/questionnaire-security/README.md) | [Guide](experiments/questionnaire-security/README.en.md) |
| Método e reprodução | [Método](experiments/questionnaire-security/docs/methodology.md) | [Methodology](experiments/questionnaire-security/docs/methodology.en.md) |
| Defesas e bateria R1 | [Defesas](experiments/questionnaire-security/docs/defenses.md) | [Defenses](experiments/questionnaire-security/docs/defenses.en.md) |
| Arquitetura e desenvolvimento | [Desenvolvimento](experiments/questionnaire-security/docs/development.md) | [Development](experiments/questionnaire-security/docs/development.en.md) |
| API e submissões | [API](experiments/questionnaire-security/docs/api.md) | [API](experiments/questionnaire-security/docs/api.en.md) |

O [experimento de currículos](docs/legacy-cv-experiment.md) tem código em
`src/recruitsecbench/`, CLI `rscb` e contratos próprios. Cada experimento é
verificado em um job de CI. Os testes usam modelos substitutos e verificam a
implementação; resultados de robustez exigem campanhas com modelos reais.
