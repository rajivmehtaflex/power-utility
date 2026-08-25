# Exa MCP Supplement Pattern (last30days example)

Reproduction recipe from a real session: `/last30days in-built model inference in browsers` on Hermes.

## Symptom
Engine footer reported `Web: 0 items (unreachable: Keyless web search unavailable)` and the cluster block said `Nothing solid this window`. The engine's keyless web floor is absent on Hermes because no BRAVE/EXA/SERPER key is configured for the *engine* (the engine's own `native_web_backend` was null). The social evidence (Reddit/HN) came back but was not enough to synthesize a real report.

## Root cause
Hermes routes web research through Exa MCP, not a built-in `WebSearch` tool. The last30days engine cannot see Exa automatically - it needs either a configured engine web key or a host WebSearch the model runs itself. So the engine's web supplement was empty and had to be backfilled by the model via Exa.

## The three Exa queries that rescued the run
Natural-language phrasing (not keyword soup), 5-8 results each:

1. `in-browser model inference WebGPU WebNN on-device AI 2026`
2. `run large language models in the browser WebGPU ONNX transformers.js 2026`
3. `browser native AI APIs device built-in model inference Chrome 2026`

These map to the skill's GENERAL/NEWS Step 2 suggestions (web context for current events + technique discussion). Exa returned usable sources (Chrome Developers built-in AI docs, Transformers.js v4, WebLLM arXiv, LiteRT.js release, WebGPU/WebNN coverage) that became the synthesis body.

## The exact append block
After the run, the saved raw file (e.g. `~/Documents/Last30Days/in-browser-model-inference-webgpu-onnx-raw-v3.md`) got this appended to satisfy the skill's Step 2.5 contract:

```markdown
## WebSearch Supplemental Results

- **Chrome Developers** (developer.chrome.com) — Built-in AI overview: the browser distributes and manages Gemini Nano; Prompt API (Chrome 148, desktop), Translator/Language Detector/Summarizer APIs (Chrome 138 stable), Writer/Rewriter/Proofreader in developer trials.
- **Oleg Maximov** (maximov.by) — Chrome 148 shipped the Prompt API on May 5 2026 exposing `window.ai` with on-device Gemini Nano (~4.27GB), Chrome-only, desktop-only, model quality = Gemini Nano not SOTA, 22GB free disk + user activation required.
- **Vadim Alakhverdov** (vadimall.com) — Transformers.js v4 makes WebGPU the default backend; Qwen2.5-0.5B at q4f16 hits ~42 tok/sec on M2 Air, ~95 tok/sec on RTX 3060; WebGPU ~10x faster than WASM.
- **Sachin Sharma** (sachinsharma.dev) — WebGPU vs WebNN 2026 deep dive: WGSL shaders, ONNX Runtime Web, quantization benchmarks, 2026 hardware support matrix.
- **Aleksei Aleinikov** (dev.to) — Browser AI in 2026: WebGPU + LiteRT.js (Google edge runtime, released July 9 2026) runs .tflite models up to 3x faster than prior web runtimes.
- **ddevtools** (ddevtools.com) — WebGPU reached full cross-browser support in January 2026 (~77% coverage per Can I Use); WebNN still behind flags, not production-ready cross-browser.
- **PyImageSearch** (pyimagesearch.com) — Running Gemma 4 multimodal in the browser with Transformers.js + WebGPU (July 2026), dtype q4f16, fully client-side.
- **WebLLM (arXiv)** (arxiv.org) — WebLLM retains up to 80% of native MLC-LLM decoding throughput on the same device.
```

## Engine invocation that worked
```bash
export LAST30DAYS_PYTHON=/Users/rajivmehtapy/.local/bin/python3.12
cd /Users/rajivmehtapy/.hermes/skills/last30days
python3 scripts/last30days.py "in-browser model inference webgpu onnx" \
  --emit=compact --save-dir="$HOME/Documents/Last30Days" --save-suffix=v3 \
  --subreddits=MachineLearning,LocalLLaMA,singularity,webdev,javascript,webgpu,onnx,tensorflow \
  --auto-resolve        # no host WebSearch -> let engine self-resolve
```
Run with `background=true` (the run exceeds the 600s foreground cap / buffers progress); read the saved raw file after completion.

## Note on the last30days skill itself
last30days is a third-party skill (mvanhorn/last30days-skill) under `~/.hermes/skills/last30days` - user/external owned, so it is NOT edited here. If it needs a structural fix (e.g. hard-coding an Exa-aware web fallback), recommend `hermes curator adopt last30days` before patching.
