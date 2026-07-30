# RecruitSecBench

Schemas de dados para avaliação reproduzível de segurança em agentes de IA que
usam ferramentas e dados de recrutamento.

O repositório define cinco conjuntos relacionados:

1. domínio: currículos, vagas e respostas;
2. benigno: tarefas legítimas e resultados esperados;
3. adversarial: prompt injections e demais ataques;
4. determinístico: tools, IDs, estados, escopos e canários;
5. auditoria: traces de execução, ground truth determinístico, rótulos humanos e
   previsões de auditor em modo sombra.

Os contratos usam JSON Schema Draft 2020-12 e validam um registro por linha de
arquivo JSONL.

Consulte a [documentação dos schemas](schemas/README.md) para o mapa de IDs,
relações entre datasets, invariantes, regras de privacidade e exemplos válidos.

## Estrutura

```text
schemas/
  common.schema.json
  domain.schema.json
  benign.schema.json
  adversarial.schema.json
  deterministic.schema.json
  audit.schema.json
  manifest.schema.json
  examples/
```

Os exemplos são inteiramente sintéticos. Canários são marcadores de teste, não
segredos reais.

## Currículos adversariais em PDF

O comando `rscb privacy generate-adversarial-cvs` deriva quatro variantes de
cada PDF previamente anonimizado em `data/redacted-restricted/`. As páginas,
dimensões e aparência permanecem inalteradas; somente uma camada de texto
invisível e extraível contendo o prompt injection é adicionada. Os derivados e
seu manifesto ficam em `data/redacted-restricted/adversarial-pdfs/`, fora do
Git e sujeitos ao mesmo controle restrito dos PDFs anonimizados.
