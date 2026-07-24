# Feature Specification: RecruitSecBench Reproducible Agentic Security Benchmark

**Feature Branch**: `002-build-recruitsecbench`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "Construir o RecruitSecBench como benchmark científico
reproduzível para os fluxos integrados de currículos e questionários, abrangendo
governança dos dados, cinco datasets, AgentDojo, baseline, intervenções CaMeL/FIDES,
auditor em modo sombra e sincronização contínua com o artigo."

## Clarifications

### Session 2026-07-22

- Q: Como definir os limites de similaridade e reidentificação que bloqueiam um perfil? → A: Definir limites numéricos universais antes da pipeline principal e aplicá-los igualmente a todos os perfis.
- Q: Qual pacote numérico universal deve ser adotado? → A: Pacote conservador: PII = 0; trecho comum normalizado ≤ 8 tokens; similaridade semântica ≤ 0,80; grupo de equivalência de quase-identificadores k ≥ 5.
- Q: Qual gate de autorização deve ser adotado para documentos reais? → A: Avaliar cada fonte e bloquear o processamento até registrar base legal aplicável, finalidade, aprovação de privacidade/ética e regras de revogação.
- Q: Qual política aplicar após revogação ou descoberta tardia de risco? → A: Quarentenar o derivado, retirá-lo de versões publicáveis, marcar manifests e runs afetados e manter somente tombstone/hash e agregados comprovadamente não identificáveis.
- Q: Qual fluxo de revisão humana deve ser adotado? → A: Um revisor primário avalia todos os perfis; um segundo revisor é obrigatório para casos marcados como incertos por ferramenta ou pelo revisor primário.
- Q: O benchmark deve usar CAMEL-AI, CaMeL ou ambos? → A: Usar somente CaMeL como defesa arquitetural contra prompt injection; CAMEL-AI fica fora da primeira versão.
- Q: Qual tecnologia chamada Fides deve entrar no benchmark? → A: Usar somente Microsoft FIDES como controle de fluxo de informação para agentes; Ethyca Fides fica fora da primeira versão.
- Q: Qual matriz experimental deve ser obrigatória? → A: Desenho fatorial 2×2 com C0 baseline, C1 CaMeL, C2 FIDES e C3 CaMeL+FIDES; o auditor roda em modo sombra sobre todas as condições.
- Q: Qual modelo de publicação deve ser adotado? → A: Publicar dados inteiramente sintéticos e artefatos experimentais; manter perfis derivados de fontes reais sob acesso controlado e aprovado.
- Q: Qual política de abertura do holdout deve ser adotada? → A: Uma campanha final após freeze completo; repetir somente falhas operacionais predefinidas e preservar todos os attempts.

### Session 2026-07-23

- Q: Qual fronteira de privacidade deve valer para PDFs anonimizados no benchmark principal? → A: Executar o benchmark privado no ambiente de produção, usando PDFs anonimizados no fluxo de avaliação da plataforma e permitindo chamadas ao mesmo provedor de modelo mediante autorização explícita por execução, sujeita aos gates formais de produção.
- Q: Como o domain deve chegar ao formato correto da plataforma? → A: Manter o domain como fonte canônica e gerar fixtures no formato nativo da plataforma por adaptador versionado e testado.

- Q: Em qual ambiente a bateria principal deve executar? → A: Produção, sujeita a autorização formal prévia, janela controlada, isolamento lógico, monitoramento e rollback; sem esses gates, a execução permanece bloqueada.

- Q: Que dados e escopo a bateria pode tocar em produção? → A: Somente projeto ou tenant dedicado, candidatos, vagas e candidaturas sintéticos do benchmark, em namespace lógico isolado; nenhum dado ou efeito sobre pessoas reais.

- Q: Qual nível de detalhe dos resultados da bateria deve ir ao artigo? → A: Publicar métricas agregadas e evidências sanitizadas por família de caso, ataque, condição e modelo; PDFs, texto extraído, prompts completos e traces detalhados permanecem sob acesso controlado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Governar e derivar perfis com segurança (Priority: P1)

Como responsável pelos dados, quero transformar aproximadamente 50 documentos
profissionais autorizados em perfis aprovados sem permitir que originais, identificadores
ou trajetórias reconhecíveis entrem no benchmark público.

**Why this priority**: Nenhum experimento é aceitável sem governança, privacidade e
controle de reidentificação antes da geração dos datasets.

**Independent Test**: Processar um lote autorizado e comprovar que somente derivados
aprovados atravessam o gate de publicação; PII, similaridade excessiva, risco de
reidentificação ou revisão ausente devem bloquear a saída.

**Acceptance Scenarios**:

1. **Given** um documento com origem, finalidade, autorização e retenção registradas,
   **When** a pipeline é executada, **Then** ela produz um derivado com evidências
   automáticas e revisão humana, sem copiar textos extensos ou a trajetória completa.
2. **Given** PII residual, identificador, similaridade acima do limite congelado ou
   combinação reidentificável, **When** a publicação é solicitada, **Then** ela é
   bloqueada com razões verificáveis.
3. **Given** um original, **When** Git, logs, prompts persistidos, traces e artefatos
   públicos são inspecionados, **Then** nenhuma cópia ou trecho indevido é encontrado.

---

### User Story 2 - Produzir os cinco datasets relacionados (Priority: P2)

Como curador, quero gerar `domain`, `benign`, `adversarial`, `deterministic` e `audit`
ligados por IDs canônicos, cobrindo currículos e questionários sem depender do produto.

**Why this priority**: Os datasets e suas relações sustentam tarefas, ataques, oráculos,
traces, métricas e claims.

**Independent Test**: Validar um cenário sintético ponta a ponta com projeto, processo,
vaga, candidato, currículo, candidatura, questionário, pergunta, resposta, sessão,
ferramenta, estado e critério, com todos os vínculos resolvidos.

**Acceptance Scenarios**:

1. **Given** registros válidos nos cinco datasets, **When** a validação cruzada roda,
   **Then** IDs, tipos, relações, escopos, estados, eventos e dependências são consistentes.
2. **Given** referência ausente, alias silencioso, vínculo cruzado, resposta na versão
   errada ou evento fora de sequência, **When** o lote é validado, **Then** ele é rejeitado
   com código determinístico.
3. **Given** questionário gerado pelo agente, **When** seus oráculos rodam, **Then**
   estrutura, cobertura, relevância, privacidade, escopo e manipulação são separados.

---

4. **Given** PDFs anonimizados aprovados e um run explicitamente autorizado, **When** o benchmark principal é executado, **Then** o ambiente de produção os processa pelo mesmo fluxo de avaliação de currículos, dentro de janela autorizada e namespace lógico isolado, registra apenas evidência sanitizada e mantém o resultado em namespace privado.

### User Story 3 - Congelar artefatos sem vazamento experimental (Priority: P3)

Como responsável pelo protocolo, quero manifests, hashes e partições por linhagem para
que desenvolvimento, piloto, avaliação e holdout sejam reproduzíveis e independentes.

**Why this priority**: Vazamento ou alteração silenciosa invalida a comparação científica.

**Independent Test**: Recriar um freeze inalterado e obter os mesmos hashes e contagens;
alterar um artefato deve exigir nova versão e impedir mistura de resultados.

**Acceptance Scenarios**:

1. **Given** registros e casos da mesma linhagem, **When** são particionados, **Then**
   todos permanecem em uma única partição.
2. **Given** `evaluation` e `holdout` congelados, **When** melhorias são desenvolvidas,
   **Then** seus conteúdos e resultados não podem orientar ajustes.
3. **Given** mudança em dado, prompt, policy, modelo, configuração ou oráculo, **When**
   um run inicia, **Then** uma nova versão identificável é exigida.

---

### User Story 4 - Validar a pipeline no AgentDojo padrão (Priority: P4)

Como pesquisador, quero executar primeiro o AgentDojo padrão sem modificar seus cenários,
para validar o harness antes de atribuir qualquer resultado ao RecruitSecBench.

**Why this priority**: Falhas operacionais não podem virar falsos resultados científicos.

**Independent Test**: Executar um smoke test de baixo custo e gerar relatório versionado
e isolado; a execução completa deve depender de solicitação explícita.

**Acceptance Scenarios**:

1. **Given** uma instalação suportada, **When** o smoke test roda, **Then** tarefas,
   ataques, defesas, persistência e relatório são verificados dentro do limite de custo.
2. **Given** um resultado do AgentDojo padrão, **When** agregados do RecruitSecBench são
   produzidos, **Then** esse resultado não é misturado nem tratado como evidência própria.
3. **Given** timeout, cancelamento ou erro, **When** o run termina, **Then** sua categoria
   operacional é preservada e não se torna SAFE, BLOCK ou sucesso de ataque.

---

### User Story 5 - Executar o baseline RecruitSecBench (Priority: P5)

Como autor, quero executar ferramentas simuladas, tarefas benignas, ataques e oráculos
nos dois fluxos antes de qualquer melhoria.

**Why this priority**: O baseline prova a validade dos ataques e ancora comparações.

**Independent Test**: Executar casos congelados com repetições e obter separadamente
utilidade, ataques, violações, vazamentos, canários, efeitos, estados, custo e latência.

**Acceptance Scenarios**:

1. **Given** datasets e protocolo congelados, **When** o baseline roda, **Then** cada
   repetição preserva caso, condição, seed, configuração, eventos e outcomes.
2. **Given** ataque sem pré-condição válida, **When** analisado, **Then** ele é inválido ou
   inconclusivo, não uma defesa bem-sucedida.
3. **Given** tarefa útil e ataque no mesmo caso, **When** agregados são calculados,
   **Then** sucesso benigno e sucesso do ataque permanecem independentes.

---

### User Story 6 - Comparar intervenções CaMeL e FIDES (Priority: P6)

Como pesquisador de segurança, quero aplicar intervenções CaMeL e Microsoft FIDES após o baseline
para testar seus efeitos sobre resistência a prompt injection, separação entre controle
e dados, privacidade, minimização e rastreabilidade.

**Why this priority**: Essas intervenções são hipóteses, não melhorias presumidas.

**Independent Test**: Reexecutar os mesmos casos de avaliação com diferenças registradas
e gerar comparação pareada de segurança, utilidade, custo, latência e revisão humana.

**Acceptance Scenarios**:

1. **Given** baseline congelado, **When** uma intervenção é aplicada, **Then** datasets,
   casos, seeds, ataques, oráculos e métricas permanecem compatíveis.
2. **Given** segurança maior e utilidade menor, **When** o resultado é escrito, **Then**
   ele é apresentado como trade-off.
3. **Given** resultados do holdout, **When** nova mudança é proposta, **Then** eles não
   podem ser usados para ajustar a intervenção.

---

### User Story 7 - Avaliar um auditor em modo sombra (Priority: P7)

Como revisor, quero comparar um auditor não interventivo com ground truth determinístico
e anotações humanas, sem expor gold labels ou dados pessoais à sua entrada.

**Why this priority**: O auditor cobre risco residual sem substituir invariantes ou
decidir sobre candidatos.

**Independent Test**: Executar o auditor sobre traces sanitizados, provar que ele não
altera o run e medir desempenho por classe contra referências externas à sua visão.

**Acceptance Scenarios**:

1. **Given** trace autorizado, **When** o auditor o recebe, **Then** sua visão exclui
   ground truth, rótulos e adjudicações.
2. **Given** uma previsão, **When** persistida, **Then** decisão, categoria, severidade,
   evidência e confiança permanecem separadas das demais fontes.
3. **Given** discordância, **When** adjudicada, **Then** os rótulos originais permanecem.

---

### User Story 8 - Sincronizar evidência e artigo (Priority: P8)

Como autor científico, quero rastrear protocolo, decisões, runs, métricas, tabelas,
gráficos e claims ao manuscrito, sem apresentar resultados não executados como conclusões.

**Why this priority**: O artigo é parte do artefato científico, não narrativa posterior.

**Independent Test**: Partir de qualquer número ou claim até seu `evidence_id`, runs,
manifest e método, e regenerar tabelas e gráficos sem editar valores manualmente.

**Acceptance Scenarios**:

1. **Given** requisito, ataque, defesa, oráculo ou métrica, **When** consultado, **Then**
   ele aponta para protocolo, evidência e seção do artigo.
2. **Given** experimento ainda não executado, **When** o manuscrito é validado, **Then**
   ele aparece apenas como objetivo, hipótese ou método.
3. **Given** resultado negativo, inconclusivo ou erro, **When** a análise é regenerada,
   **Then** ele permanece disponível e não é descartado silenciosamente.

### Edge Cases

- Autorização revogada ou retenção expirada após criação de derivados.
- Perfil sem PII direta, mas com trajetória rara ou texto pesquisável.
- Dois originais produzindo derivados excessivamente semelhantes.
- Lote final diferente do alvo de 50 por bloqueios de privacidade.
- Registro válido isoladamente, mas ligado a entidade de outra partição.
- Mesma linhagem disfarçada por aliases do produto.
- Questionário de vaga ainda sem candidatura ou resposta em versão aposentada.
- Ataque distribuído entre documentos, RAG, memória e sessão.
- Retry causando efeito ou transição duplicada.
- Canário presente no contexto, mas ausente da saída final.
- Mudança de versão ou comportamento do AgentDojo padrão.
- Provedor sem seed determinística ou instável entre repetições.
- Intervenção incompatível com parte do baseline.
- Auditor abstendo-se ou falhando em classe rara.
- Discordância humana ou PII descoberta em trace.
- Script de artigo encontrando runs incompatíveis ou evidência ausente.
- Consulta acidental ao holdout antes do momento protocolado.

## Requirements *(mandatory)*

### Functional Requirements

#### Governança e privacidade dos dados

- **FR-001**: Antes de qualquer processamento, cada original MUST registrar origem,
  finalidade específica, controlador e responsável, base legal aplicável à fonte,
  evidência de autorização quando exigida, aprovação de privacidade/ética, retenção e
  regras de revogação. Ausência ou reprovação de qualquer item MUST bloquear a entrada.
- **FR-002**: Originais MUST permanecer em área local restrita e fora de Git, datasets,
  logs, prompts persistidos, traces e artefatos publicados.
- **FR-003**: Originais MUST NOT ser enviados automaticamente a provedores externos nem
  usados diretamente em experimentos públicos.
- **FR-003a**: PDFs anonimizados aprovados MAY ser usados no benchmark principal privado pelo fluxo de avaliação de currículos no ambiente de produção somente após autorização formal prévia, janela controlada, isolamento lógico, monitoramento e plano de rollback. Chamadas ao provedor de modelo configurado em produção exigem autorização explícita por run, configuração e versão registradas, finalidade compatível, controle de acesso e rastreabilidade; seus conteúdos e resultados detalhados MUST permanecer fora de Git, datasets públicos e artefatos publicados.
- **FR-003b**: Toda bateria executada em produção MUST operar exclusivamente em projeto ou tenant dedicado e namespace lógico isolado, com candidatos, vagas, candidaturas, questionários e efeitos sintéticos do benchmark. A suite MUST recusar referências a pessoas reais e MUST NOT alterar avaliação, ranking, estado ou decisão de qualquer pessoa real.
- **FR-004**: O projeto MUST NOT realizar scraping ou coleta automatizada no LinkedIn.
- **FR-005**: A derivação MUST remover ou substituir todos os identificadores diretos
  enumerados nesta feature.
- **FR-006**: A derivação MUST generalizar, transformar ou suprimir identificadores
  indiretos e combinações raras com risco de reidentificação.
- **FR-007**: Derivados MUST NOT copiar frases extensas, descrições reconhecíveis ou
  trajetórias completas dos originais.
- **FR-008**: Cada derivado MUST passar por detecção de PII e identificadores, similaridade,
  risco combinatório, validação estrutural e revisão humana primária. Casos marcados como
  incertos por qualquer ferramenta ou pelo revisor primário MUST receber uma segunda
  revisão independente; publicação MUST permanecer bloqueada até a decisão secundária.
- **FR-009**: Limites numéricos universais de similaridade e risco de reidentificação MUST
  usar o pacote conservador: zero detecções de PII ou identificadores; maior trecho comum
  normalizado com o original de no máximo 8 tokens; similaridade semântica de no máximo
  0,80; e grupo de equivalência de quase-identificadores com `k >= 5`. Tokenização,
  normalização, modelo de similaridade, quase-identificadores e versão das ferramentas
  MUST ser documentados, versionados, congelados antes da pipeline principal e aplicados
  igualmente a todos os perfis.
- **FR-010**: PII residual, similaridade excessiva, risco relevante ou revisão ausente
  MUST bloquear qualquer liberação. Somente dados inteiramente sintéticos, schemas,
  casos, código, protocolo e resultados sanitizados MAY ser públicos. Perfis derivados
  de fontes reais, mesmo aprovados, MUST permanecer em acesso controlado por solicitação,
  finalidade compatível, aprovação, menor privilégio, registro de acesso e revogação.
- **FR-011**: Revogação, expiração ou reprovação posterior MUST bloquear novo uso,
  colocar o derivado e evidências detalhadas em quarentena, removê-los de versões
  publicáveis e marcar manifests e runs afetados. Somente tombstone com IDs técnicos,
  hashes, motivo e datas e agregados comprovadamente não identificáveis MAY permanecer;
  o conteúdo derivado MUST NOT permanecer acessível ou ser reutilizado.

#### Modelo canônico e dataset domain

- **FR-012**: O modelo MUST representar projeto, processo, vaga, candidato, currículo,
  candidatura, questionário, pergunta, resposta, sessão, ferramenta, estado e critério.
- **FR-013**: `application`, `questionnaire` e `question` MUST possuir registros canônicos
  completos no dataset `domain`.
- **FR-014**: Vínculos MUST garantir toda a ancestralidade e cardinalidade descritas pelo
  usuário, incluindo resposta ligada a pergunta, questionário, candidatura, candidato e vaga.
- **FR-015**: Toda operação MUST declarar ator e escopo aplicável.
- **FR-016**: IDs canônicos MUST permanecer estáveis; aliases do produto MUST NOT duplicar
  ou substituir campos silenciosamente.
- **FR-017**: Currículos, vagas, candidaturas, questionários, perguntas e respostas MUST
  conter todos os atributos definidos em Required Domain Field Coverage.
- **FR-018**: Versões e históricos MUST manter respostas e evidências atribuíveis após
  mudanças de estado ou novas versões.

#### Datasets benign e adversarial

- **FR-019**: `benign` MUST cobrir geração e gestão de questionários, busca e conversa de
  currículos, avaliação, RAG, tools, estados e análise de respostas.
- **FR-020**: Cada caso benigno MUST declarar ator, escopo, entradas, fixtures, estado,
  solicitação, ações permitidas, dados autorizados, outcome, oráculos, estados finais,
  limite de efeitos e métricas.
- **FR-021**: Questionários MUST ter oráculos separados de estrutura, cobertura,
  relevância, privacidade, escopo, auditabilidade e mudança não autorizada.
- **FR-022**: `adversarial` MUST cobrir todas as famílias definidas em Required Attack Coverage,
  incluindo injections, score, tools, IDs, escopo, PII, sessão, estado, RAG, auditor e
  manipulação de questionários e respostas.
- **FR-023**: Superfícies MUST incluir vaga, currículo, candidatura, questionário,
  pergunta, resposta, RAG, sessão, ferramenta, MCP, estado e auditor.
- **FR-024**: Casos adversariais MUST referenciar equivalentes benignos quando existirem.
- **FR-025**: Cada ataque MUST definir validade, objetivo, resultado proibido, severidade,
  decisão esperada, oráculos e evidências.

#### Datasets deterministic e audit

- **FR-026**: `deterministic` MUST fornecer fixtures de tools, IDs, relações, acesso,
  estados, permissões, escopos, sessões e canários para todas as entidades.
- **FR-027**: Cada operação MUST declarar ator, estado, argumentos, decisão, código,
  argumentos normalizados, próximo estado e efeitos esperados.
- **FR-028**: Canários MUST ser sintéticos e detectados separadamente em recuperação,
  contexto, argumentos, resultados, saída e trace.
- **FR-029**: `audit` MUST registrar run, caso, condição, repetição, modelo, configuração,
  seed, status, eventos, tools, policies, estados, efeitos, canários e três fontes de outcome.
- **FR-030**: Traces MUST NOT armazenar originais, PII, prompts integrais sensíveis ou
  gold outcomes dentro da visão do auditor.
- **FR-031**: Falhas operacionais MUST permanecer separadas de outcomes de utilidade,
  ataque, policy e auditoria.

#### Manifests, partições e validação

- **FR-032**: Cada dataset MUST ter manifest com nome, versão, schema, contagens,
  partições, SHA-256, dependências, origem, seed, geração, privacidade e publicação.
- **FR-033**: Partições MUST ser `development`, `pilot`, `evaluation` e `holdout`.
- **FR-034**: A unidade de particionamento MUST ser a linhagem conectada; registros,
  variantes e casos relacionados MUST permanecer juntos.
- **FR-035**: `evaluation` e `holdout` MUST ser congelados antes das intervenções. O
  `holdout` MUST permanecer selado até uma única campanha final, iniciada somente após o
  freeze de protocolo, código, datasets, prompts, policies, modelos e configurações.
  Reexecução MAY ocorrer apenas para classes de falha operacional predefinidas no
  protocolo; todos os attempts, inclusive falhos, MUST ser preservados e vinculados.
- **FR-036**: A pipeline MUST validar Draft 2020-12, IDs, referências, tipos, escopos,
  estados, eventos, hashes, manifests, dependências, canários, privacidade, similaridade,
  isolamento, cobertura e consistência de outcomes.
- **FR-037**: A validação MUST produzir relatório humano e saída estruturada para gates.
- **FR-038**: Mudança em artefato congelado MUST gerar nova versão e impedir agrupamento
  silencioso de resultados incompatíveis.

#### AgentDojo e ambiente RecruitSecBench

- **FR-039**: A pipeline MUST executar primeiro o AgentDojo padrão sem modificar cenários
  e manter seus resultados separados.
- **FR-040**: MUST existir smoke test padrão de baixo custo; execução completa exige ação
  explícita.
- **FR-041**: Runs padrão MUST registrar versão, suites, tarefas, ataques, defesas,
  modelo, parâmetros, seed, repetições, custo, latência e erros.
- **FR-042**: A suíte personalizada MUST fornecer ambiente, estado determinístico, tools,
  atores, permissões, tarefas, injections, ataques, defesas, oráculos, efeitos e traces.
- **FR-043**: Tools simuladas MUST cobrir currículos, vagas, questionários, respostas,
  avaliações, estados, candidaturas, sessões e RAG.
- **FR-044**: Conteúdo, memória, recuperação e respostas MUST ser dados sem autoridade
  para alterar policy, identidade, escopo ou permissão.

#### Baseline, intervenções e medição

- **FR-044a**: Uma fase posterior MUST transformar o domain canônico em fixtures no formato nativo da plataforma, por adaptador versionado e testado contra seus contratos. O adaptador MUST preservar IDs, escopos, versões, linhagem e resultados esperados, sem substituir silenciosamente o artefato canônico.
- **FR-045**: O baseline MUST preceder intervenções e usar artefatos e partições congelados.
- **FR-046**: Cada condição MUST preservar repetições e separar utilidade, ataque, policy,
  escopo, vazamento, canários, efeitos, estados, custo e latência.
- **FR-047**: Agregação MUST ocorrer por `case_id`, quantificar incerteza e não tratar
  repetições como casos independentes.
- **FR-048**: Ataques MUST demonstrar validade no baseline antes de claims de defesa.
- **FR-049**: CaMeL MUST ser testado como defesa contra prompt injection, separando
  controle confiável de dados não confiáveis e mantendo autoridade de tools fora do
  conteúdo processado pelo modelo, sem presumir benefício.
- **FR-050**: Microsoft FIDES MUST ser testado como controle de fluxo de informação para
  agentes, incluindo rótulos de confidencialidade e integridade, propagação de rótulos,
  enforcement determinístico de policies e restrições de fluxo, sem presumir benefício.
- **FR-051**: A matriz principal MUST usar o desenho fatorial `2×2`: `C0` baseline sem
  CaMeL/FIDES, `C1` somente CaMeL, `C2` somente FIDES e `C3` CaMeL+FIDES. Cada condição
  MUST registrar identidade, versão, configuração e diferenças.
- **FR-052**: Comparações MUST preservar casos, seeds, ataques, oráculos e métricas; o
  holdout MUST NOT orientar ajustes.
- **FR-053**: Segurança, utilidade, custo, latência, estabilidade e revisão humana MUST
  ser reportados juntos como trade-offs.

#### Auditor e artigo científico

- **FR-054**: O auditor MUST operar em modo sombra sobre `C0`, `C1`, `C2` e `C3`, sem
  integrar o tratamento experimental, bloquear, alterar estado ou decidir sobre candidatos.
- **FR-055**: Sua visão MUST ser sanitizada, minimizada e excluir ground truth, rótulos e
  adjudicações.
- **FR-056**: Sua saída MUST conter decisão, categoria, severidade, evidência e confiança,
  separadas dos demais outcomes.
- **FR-057**: Cada item gold MUST ter ao menos duas anotações humanas independentes;
  discordâncias e adjudicação MUST preservar originais.
- **FR-058**: Desempenho MUST ser reportado por classe, incluindo erros e abstenções.
- **FR-059**: O repositório MUST manter protocolo, threat model, dicionário, taxonomia,
  privacidade, revisão, decisões, configurações, rastreabilidade, limitações, validade,
  tabelas, gráficos, agregados e reprodução sincronizados com o artigo.
- **FR-060**: Cada requisito, dataset, caso, ataque, defesa, oráculo e métrica MUST ligar-se
  ao protocolo, evidência e seção do artigo.
- **FR-061**: Cada número ou claim observado MUST apontar para `evidence_id` e artefato
  imutável regenerável.
- **FR-061a**: O artigo MUST publicar somente métricas agregadas e evidências sanitizadas por família de caso, ataque, condição e modelo. PDFs anonimizados, texto extraído, prompts completos, traces detalhados e resultados individuais permanecem em acesso controlado, vinculados a manifestos e evidence IDs.
- **FR-062**: O artigo MUST distinguir objetivo, hipótese, método, resultado, interpretação
  e limitação; resultado não executado MUST NOT aparecer como conclusão.

### Required Privacy Coverage

- **Identificadores diretos**: nome, email, telefone, endereço, fotografia, URLs,
  identificadores de redes sociais, usernames, números de documentos e identificadores
  únicos MUST ser removidos ou substituídos.
- **Identificadores indiretos**: localização, datas, empresas, instituições, cargos
  específicos, projetos, certificações, publicações, trajetórias raras, combinações
  incomuns de competências e idiomas ou tecnologias raros MUST ser generalizados,
  transformados ou suprimidos quando elevarem risco de reidentificação.
- **Similaridade pesquisável**: frases extensas, descrições reconhecíveis e trajetórias
  completas MUST ser consideradas tanto na análise automática quanto na revisão humana.

### Required Domain Field Coverage

- **Currículo**: candidato anônimo, área, senioridade, documentos derivados, idioma,
  texto aprovado, dados estruturados, competências, experiências e formação
  generalizadas e canários sintéticos aplicáveis.
- **Vaga**: ID, título, descrição, senioridade, requisitos, competências, critérios,
  pesos, processo seletivo e variantes controladas.
- **Candidatura**: ID, candidato, vaga, processo, estado atual, histórico relevante,
  escopo, questionário associado e permissões.
- **Questionário**: ID, vaga, processo, versão, finalidade, status, responsável, escopo,
  critérios usados, perguntas ordenadas, regras de acesso e atualização e metadados de
  geração e aprovação.
- **Pergunta**: ID, texto, tipo de resposta, competência ou critério, justificativa de
  relevância, obrigatoriedade, ordem, rubrica, restrições de privacidade e revisão.
- **Resposta**: candidatura, candidato, vaga, questionário, pergunta, texto ou referência
  aprovada, qualidade esperada e vínculo adversarial aplicável.

### Required Attack Coverage

- **Prompt injection**: direta e indireta em currículo, vaga, resposta, questionário,
  pergunta e conteúdo recuperado.
- **Decisão e conteúdo**: manipulação de pontuação; favorecimento ou prejuízo de
  candidatos; perguntas fora do escopo; solicitação indevida de PII; alteração não
  autorizada de perguntas, critérios, pesos e respostas.
- **Ferramentas e identidade**: uso não autorizado de tools, alteração de argumentos,
  substituição de IDs e acesso a candidatura ou questionário de outro processo.
- **Dados e recuperação**: acesso entre escopos, exfiltração de documentos, vazamento de
  PII, envenenamento de RAG e exposição de canários.
- **Sessão, estado e persistência**: reutilização e replay de sessão, manipulação e
  transição inválida de estado e persistência duplicada.
- **Auditoria**: evasão ou manipulação do auditor e tentativa de inserir ground truth ou
  rótulos humanos em sua visão.

### Key Entities *(include if feature involves data)*

- **Source Document / Privacy Review**: Original restrito e evidências automáticas e
  humanas que controlam sua derivação.
- **Project / Hiring Process / Vacancy**: Hierarquia canônica de contexto, requisitos,
  critérios, pesos e autorização.
- **Candidate / Derived CV / Application**: Identidade lógica anônima, perfil aprovado e
  vínculo com vaga, processo, estado, escopo e permissões.
- **Questionnaire / Question / Candidate Response**: Avaliação versionada, perguntas e
  respostas ligadas aos critérios e ao escopo.
- **Agent Session / Tool / Process State**: Contexto, capacidade e estado verificáveis.
- **Benign Case / Adversarial Case**: Tarefa legítima e ataque comparável com outcomes
  separados.
- **Deterministic Fixture / Canary**: Estado e marcador sintético verificáveis por máquina.
- **Audit Trace / Auditor View**: Registro sanitizado e seu subconjunto autorizado.
- **Artifact Manifest / Partition Lineage**: Inventário congelado e grupo indivisível que
  controla versão, hash, dependência e isolamento.
- **Experiment Run / Condition / Repetition**: Execução identificável com inputs,
  configuração, falhas e outcomes brutos.
- **Human Annotation / Adjudication / Auditor Prediction**: Fontes separadas de julgamento.
- **Evidence / Claim Link**: Relação entre protocolo, artefato, resultado e manuscrito.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A primeira versão registra resultado de privacidade para 50 documentos ou
  justificativa protocolada para diferença do alvo.
- **SC-002**: 100% dos perfis derivados liberados para uso experimental controlado têm
  aprovação humana, ausência de PII detectável e atendem simultaneamente a trecho comum
  normalizado ≤ 8 tokens, similaridade semântica ≤ 0,80 e `k >= 5` nos
  quase-identificadores congelados.
- **SC-003**: Zero originais, perfis derivados de fontes reais, PII, credenciais, prompts
  sensíveis ou trajetórias reconhecíveis aparecem no Git, datasets públicos ou traces.
- **SC-004**: 100% das entidades mínimas têm representação canônica e exemplos válidos;
  100% das fixtures inválidas são rejeitadas pelo motivo esperado.
- **SC-005**: Os cinco datasets são gerados e validados com manifests, hashes e contagens
  reproduzíveis para o mesmo freeze.
- **SC-006**: Nenhuma linhagem cruza partições; `evaluation` e `holdout` passam por teste
  automatizado de isolamento, e o log do holdout demonstra uma única campanha final com
  retries limitados às falhas operacionais predefinidas e todos os attempts preservados.
- **SC-007**: Toda tarefa e família de ataque obrigatória possui caso executável, oráculos
  e contraparte benigna quando aplicável.
- **SC-008**: 100% dos questionários geram outcomes separados de estrutura, cobertura,
  relevância, privacidade, escopo e manipulação.
- **SC-009**: O smoke test padrão conclui execução e relatório em namespace isolado.
- **SC-010**: A suíte personalizada executa cenário ponta a ponta de cada fluxo com tools,
  estados, efeitos, traces, utilidade e segurança verificáveis.
- **SC-010a**: Para cada caso principal autorizado com PDF anonimizado, a suíte privada comprova ingestão pelo fluxo da plataforma, associação ao escopo correto, execução da bateria benigna/adversarial e retenção somente de evidência sanitizada vinculada ao manifesto do run.
- **SC-010b**: 100% dos runs em produção recusam referências a pessoas reais e comprovam que todas as leituras, escritas e efeitos permaneceram no projeto ou tenant sintético dedicado.
- **SC-011**: O baseline preserva todas as repetições e suporta todas as métricas exigidas
  por `case_id`.
- **SC-012**: 100% das falhas operacionais permanecem separadas de outcomes científicos.
- **SC-013**: `C0`, `C1`, `C2` e `C3` são comparáveis por manifest no desenho `2×2`, sem
  uso do holdout para ajuste, e possuem previsões sombra do auditor separadas dos outcomes.
- **SC-014**: Toda comparação apresenta segurança, utilidade, custo, latência, estabilidade
  e revisão humana conjuntamente.
- **SC-015**: O auditor não altera nenhum run e recebe zero gold outcomes ou rótulos.
- **SC-016**: 100% dos itens gold têm duas anotações independentes e preservam discordância.
- **SC-017**: Tabelas e gráficos são regenerados de runs brutos sem edição manual de valores.
- **SC-018**: 100% dos claims quantitativos observados apontam para `evidence_id`; claims
  planejados são marcados como hipótese ou método.
- **SC-018a**: 100% dos resultados publicados no artigo são agregados sanitizados por família de caso, ataque, condição e modelo e apontam para evidência controlada compatível.
- **SC-019**: Revisor independente reproduz validação, smoke test, suíte e análise sem
  acesso aos originais.
- **SC-020**: A primeira versão satisfaz todos os gates de privacidade, contratos,
  datasets, pipeline, baseline, intervenções, auditor e evidência desta spec.

## Assumptions

- O gate de privacidade prevalece sobre completar artificialmente o alvo de 50 documentos.
- Apenas derivados sintéticos ou aprovados entram no workspace versionado e no harness.
- A unidade de particionamento é a linhagem conectada; `evaluation` e `holdout` são selados.
- Relevância ambígua pode exigir revisão humana, mas não anula falhas determinísticas.
- O benchmark principal privado pode usar PDFs anonimizados aprovados no fluxo da plataforma em produção somente após autorização formal, janela controlada, isolamento lógico, monitoramento e rollback; chamadas ao provedor exigem autorização explícita por run e seus detalhes não são publicados.
- O domain canônico será convertido posteriormente, por adaptador versionado, para fixtures no formato nativo da plataforma; essa conversão não substitui o corpus canônico.- AgentDojo padrão valida somente o harness e não produz resultados RecruitSecBench.
- CaMeL e Microsoft FIDES são intervenções experimentais fornecidas pelo protocolo;
  versão e configuração serão congeladas no planejamento e não implicam eficácia.
  CAMEL-AI multiagente e Ethyca Fides ficam fora de escopo na primeira versão.
- Duas anotações independentes por item gold são o mínimo para medir discordância.
- Execuções completas ou com custo relevante exigem ação explícita; smoke tests têm limites.
- Scraping, PII pública, originais públicos, interface web, ATS/HRIS, decisões reais,
  contratação automática, fine-tuning e claims não observados ficam fora de escopo.

## Security, Research Integrity & Production Boundaries *(mandatory)*

### Threat Model and Authorization

- **Assets and affected people**: Originais, derivados, candidatos, questionários,
  critérios, tools, memória, RAG, sessões, estados, manifests, revisores e artigo.
- **Adversaries and capabilities**: Conteúdo hostil pode entrar por qualquer superfície e
  tentar manipular IDs, tools, argumentos, score, critérios, estado, privacidade e auditor.
- **Authorized scope**: Toda ação é limitada por ator, projeto, processo, vaga,
  candidatura, candidato, questionário, sessão, tool e estado aplicáveis.
- **Untrusted inputs**: Documentos, textos, RAG, memória e saídas de modelo, tools e
  auditor são dados sem autoridade de policy.
- **Deterministic invariants**: IDs, relações, tipos, permissões, argumentos, estados,
  escopos, versões, hashes, partições, eventos, efeitos e canários.

### Evidence and Measurement

- **Research questions / planned claims**: O benchmark reproduz ataques nos dois fluxos?
  As intervenções alteram segurança sem destruir utilidade? Que risco residual o auditor
  detecta, com quais erros e custos?
- **Baseline and comparison conditions**: Baseline precede intervenções; condições usam
  casos congelados e diferenças versionadas; holdout não orienta ajustes.
- **Security and utility measures**: Utilidade, ataque, policy, escopo, vazamento,
  canários, efeitos, estados, auditor, latência, tokens, custo e revisão humana.
- **Failure taxonomy**: Caso inválido, falha benigna, ataque, policy, revisão, provedor,
  harness, timeout, cancelamento e inconclusivo permanecem distintos.
- **Reproducibility artifacts**: Protocolo, dados, casos, fixtures, prompts, policies,
  modelos, seeds, manifests, hashes, runs, análises, tabelas e gráficos.

### Privacy and Human Accountability

- **Data provenance and authorization**: Fonte legítima documentada, originais restritos
  e derivados sujeitos a automação, limites congelados e revisão humana.
- **Minimization, retention, and publication**: Somente evidência sanitizada mínima é
  armazenada; retenção e revogação são rastreáveis; risco bloqueia publicação.
- **Human-review and contestation path**: Privacidade, relevância e rótulos ambíguos são
  revistos por responsáveis, preservando decisões e discordâncias.
- **Prohibited outcomes**: Scraping, PII pública, exfiltração, mudanças não autorizadas e
  qualquer contratação, rejeição ou ranking real automatizado.

### Maturity Boundary

- **Current status**: Artefato científico e ambiente experimental, não produção.
- **Explicit non-goals**: Segurança completa, prova formal, eficácia presumida de CaMeL,
  FIDES ou auditor, integração produtiva e decisões reais.
- **Required gate**: Escopo, privacidade, protocolo, baseline, controles, auditoria e
  publicação são obrigatórios; produção futura exige aprovação separada.
