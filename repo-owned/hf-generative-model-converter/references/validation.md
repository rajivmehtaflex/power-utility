# Validation — reference checks, staged reload, and packaging gates

Validation converts "a file appeared" into "the converted model works". Two evidence classes are kept
separate throughout: **functional smoke** (runs, terminates cleanly, correct file inventory) and
**numerical fidelity** (comparable output against the native reference). Smoke passing never implies
fidelity; report both independently.

## Fixtures come first

Freeze fixtures, expectations, tolerances, metric, and per-phase timeout budget **before** inspecting
any converted output:

- Three synthetic text prompts per recipe, including one near the profile's context limit.
- Decoding fixed: batch 1, greedy, explicit seed where the runtime supports it, bounded new tokens
  (default 32).
- Expectations recorded as observable properties (nonempty output, clean EOS or bound termination, no
  runtime errors, no nonfinite values where observable) plus the recorded raw reference outputs.
- The same tokenizer/template/preprocessing settings as the reference pipeline; record them.
- Fixture identifiers and hashes go into the manifest's validation records; fixture content itself
  stays in the run workspace, not in the package.

## Reference and target comparison

1. Run the pinned native reference (source model, unconverted) under the frozen settings; record its
   outputs and phase timings (timings are observations, never a benchmark claim).
2. Run the converted model on the same runtime/recipe with identical inputs.
3. Compare using the metric and threshold declared in the recipe **before** conversion. Never relax a
   threshold after a failure — a failed parity check is a failed validation, or, if the metric is
   genuinely incomparable, fidelity is reported `unverified` and the reason recorded.
4. Quantized recipes (any future profile) require explicit precision-appropriate acceptance criteria in
   their recipe; the F16 default still uses the reference comparison above.

## VLM checks (when a VLM recipe is verified)

A VLM-verified claim requires: two controlled synthetic images with distinct expected answers and one
identical prompt; the reference model must pass both first; then the converted pipeline must pass both.
No VLM check may be replaced by text-only inference.

## Staged reload — package independence

Before publication, reload the **staged copy** with:

- the original source checkout unavailable (different working directory; source paths not present),
- model-download traffic disabled using the runtime's supported settings (`HF_HUB_OFFLINE=1` and
  equivalent local-only flags), and
- file-access evidence recorded (no dependence on original weights, hidden caches, or absolute paths
  from the conversion host).

If OS-level network denial was not exercised, state that limitation in the report.

## Packaging

Stage only: target artifacts, required processor/tokenizer/config files, licenses and notices, the
destination model card (from [../assets/model-card.md](../assets/model-card.md)), and sanitized
evidence summaries. Copy no source/build trees, no caches, no secrets.

Then, using [../scripts/artifact_manifest.py](../scripts/artifact_manifest.py):

```bash
python scripts/artifact_manifest.py build --stage <stage-dir> --metadata <metadata.json> --out <stage-dir>/artifact-manifest.json
python scripts/artifact_manifest.py verify --stage <stage-dir> --manifest <stage-dir>/artifact-manifest.json
```

`verify` must pass immediately before upload: exact file set, checksums match, schema/required fields
present, recipe/profile identity matches the run, and required validation gates are recorded as
passed. The manifest excludes its own hash; the publication receipt (outside the staged inventory)
records the manifest hash and remote commit.

## Failure handling

- Any failed gate: stop before the next phase; keep run logs in the run workspace.
- Re-run validation from scratch after any change to artifact bytes, profile, recipe, or toolchain.
- Report `failed`/`pending`/`blocked` with the reason; never reclassify to make a report look complete.
