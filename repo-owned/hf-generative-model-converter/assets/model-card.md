# Destination model card template

Fill every bracketed field from recorded run evidence. Do not invent values; if a value is unknown,
write `unknown — <why>`. Keep the license section verbatim-faithful to the source model's terms.

```markdown
---
license: <source-model license identifier, e.g. apache-2.0>
base_model: <source model id>
base_model_revision: <immutable commit sha>
library_name: <runtime, e.g. llama.cpp>
tags:
  - gguf
  - converted
  - hf-generative-model-converter
---

# <model name> — GGUF conversion

Converted locally from [<source id>@<short sha>](<source url>/tree/<revision>) on <UTC date> by the
`hf-generative-model-converter` skill. This card is generated from the run manifest; conversion
commands and toolchain pins are recorded in the source repository's recipe evidence.

## Files

| File | Size | SHA-256 (first 12) |
|---|---|---|
| <filename> | <bytes> | <hash12> |

## Conversion profile

- Precision: <outtype> (quantization: <none / user-requested step>)
- Context profile: <tokens>; batch: <n>
- Chat template: <source template name / "preserved from tokenizer_config.json">
- Exporter/toolchain: <converter> at revision <sha>, source-built (<build key>)

## Intended use and runtime

<Workload recorded for the recipe — e.g. text input → generated text, chat via the preserved template.>
Requires <runtime> >= <version>. Verified on Linux x86_64 CPU; other hosts/backends unverified.

## Validation summary

- Fixtures: <n> synthetic prompts (frozen before evaluation), including one near the context limit.
- Reference comparison: <metric> = <measured value> (threshold <t>, declared before conversion).
- Functional smoke: <pass/fail — EOS termination, no runtime errors>.
- Numerical fidelity: <verified + value | unverified — reason>.
- Staged reload: <pass — source weights unavailable, hub downloads disabled>.

## Limitations

- <Recorded recipe limitations, e.g. CPU-only verification; F16 master profile; single-host evidence.>

## License and attribution

Source model terms: <license + URL to terms>. This conversion redistributes model weights under those
terms<, with recorded permission: <reference>, if applicable>. Runtime/toolcode notices: <llama.cpp MIT
notice included in the package>.
```
