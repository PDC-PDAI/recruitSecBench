# RecruitSecBench — previous experiment

[🇧🇷 Português](legacy-cv-experiment.md) · 🇺🇸 **English** · [Home](../README.en.md)

The previous root implementation defines reproducible security datasets for
recruitment agents using tools and recruitment data. It is preserved independently
from the new questionnaire pipeline.

Five related datasets cover domain (CVs, jobs, answers), benign tasks and expected
outcomes, adversarial attacks, deterministic tools/IDs/states/scopes/canaries,
and audit execution traces, ground truth, human labels, and shadow auditor predictions.

Contracts use JSON Schema Draft 2020-12, one record per JSONL line. See the original
[schema documentation](../schemas/README.md) for IDs, relations, invariants, privacy
rules, and synthetic examples. Canaries are test markers, not real secrets.

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

The existing `rscb privacy generate-adversarial-cvs` command derives four variants
of each previously anonymized PDF in `data/redacted-restricted/`. It adds an
invisible extractable injection text layer while preserving pages, dimensions,
and appearance. Derivatives/manifests remain in
`data/redacted-restricted/adversarial-pdfs/`, outside Git under the same restricted
access controls. This workflow is not used by the new questionnaire experiment.
