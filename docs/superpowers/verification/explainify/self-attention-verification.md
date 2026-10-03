# Self-attention explainer video — verification record

Run directory: `explainify-output/self-attention-20261002-221152/` (repo: `power-utility`, branch `main`, uncommitted tree)
Produced: 2026-10-02. Task: prove the `explainify` renderer template generalizes to the self-attention topic via the skill's own workflow (plan §4 brief, §6 storyboard contract, §7 verification).

Artifacts in this directory:

- `self-attention-storyboard.json` — storyboard with embedded teaching brief (8 scenes, 42.00 s total).
- `self-attention-render.py` — adapted copy of `repo-owned/explainify/scripts/render_video.py` (EMBEDDED_SCHEMA byte-identical; CLI, validation, encoding, output guard unchanged).
- `self-attention-explainer.mp4` — the rendered video.
- `frames/` — 12 extracted verification PNGs.

## 1. Teaching checks

- **Learning objective met?** Yes. The video shows, in order: tokens as vectors → q/k/v projections → one query scored against every key with the √d scaling → softmax into weights summing to 1 → weighted sum forming the new vector for "it" → all tokens in parallel → the closing formula `Attention(Q,K,V) = softmax(QKᵀ/√d)V`. The pronoun-resolution objective is delivered in the weighted-sum scene's payoff line (verified on frame: `"it" now carries mostly "cat" — the reference is resolved`).
- **Prerequisites introduced?** Yes. Vectors are introduced in scene 2 ("Each word is a vector of numbers", plus "in a real model: hundreds of numbers, one per dimension"); weights summing to 1 are introduced in scene 5 with the on-screen equation `Σ_j w_ij = 1` and the caption "each query's weights sum to 1".
- **Qualifications preserved?** Yes. On-screen/in-storyboard: scores scene footer "illustrative scores"; softmax and weighted-sum scene footers "illustrative weights"; closing footer "weights in this video are illustrative · silent · rendered locally"; parallel scene states "(one attention head — real models run several in parallel)". All 9 claims carry `origin: model-knowledge` with qualifications where needed (this is a topic run; no external source).
- **Mechanism correct?** Yes. Mechanism steps 1–7 in the brief match the scene sequence; the score equation shown is `s_ij = q_i·k_j/√d_k` and the final formula matches claim `claim-attention-formula`.
- **Example arithmetic consistent?** Verified with NumPy against the storyboard JSON:
  - `weights_matrix` is 7×7; every row sums to exactly 1.0 (`row sums: [1. 1. 1. 1. 1. 1. 1.]`, `allclose → True`); minimum value 0.02 (non-negative).
  - `softmax(scores)` for the "it" row `[0.8, 4.1, 1.6, 0.3, 1.9, 0.5, 1.2]` = `[0.028, 0.749, 0.062, 0.017, 0.083, 0.020, 0.041]`; rounded to 2 decimals it equals the storyboard `it` row `[0.03, 0.75, 0.06, 0.02, 0.08, 0.02, 0.04]` exactly, which also equals the `weighted-sum` scene's `weights_row` (sum 1.0). Argmax is index 1 = "cat" (0.75). The on-screen numbers (score "4.1", weight "0.75", bars ×0.03/×0.75/×0.06/×0.02/×0.08/×0.02/×0.04) all match the storyboard data.
- **Values labeled illustrative?** Yes — `value_origin: "illustrative"` in the brief's example, `must_preserve` records it, and three scenes carry the label on screen.

## 2. Scene-check table (12 frames extracted, 12 inspected)

| Scene (id) | Span (s) | Frame inspected | Finding |
|---|---|---|---|
| title | 0.0–4.0 | `frame-title.png` @ 3.8 s | PASS. Large "Self-attention" title, blue subtitle "How does a model know what "it" means?", all 7 token boxes legible with distinct colors; red ring correctly around "it"; grey closing line present; no clipping, no overlap, no artifacts. |
| tokens-as-vectors | 4.0–9.0 | `frame-tokens-as-vectors.png` @ 8.4 s | PASS. All 7 tokens with connector lines and 4-cell vector strips; example row `cat → [ 0.20 −1.30 0.75 ⋯ 0.42 ]` renders fully in Computer Modern (minus sign and ellipsis present, no missing glyphs); grey dimension note below; no clipping/overlap. |
| qkv-projections | 9.0–15.0 | `frame-qkv-projections.png` @ 14.0 s | PASS. Three rows of small q (yellow), k (blue), v (green) boxes under every token with grey connector arrows; left row labels q/k/v; three legend lines ("what am I looking for?" / "what do I offer for matching?" / "what do I hand over?") legible and color-matched; no clipping/overlap. |
| query-scores-keys | 15.0–21.5 | `frame-query-scores-keys.png` @ 19.9 s | PASS. "it" ringed red; yellow "q" box below it; 7 blue "k" boxes; curved arrows with visibly varying widths, thickest to "cat" (yellow); scores 0.8 / **4.1** / 1.6 / 0.3 / 1.9 / 0.5 / 1.2 shown, 4.1 highlighted yellow; equation `s_ij = q_i·k_j / √d_k` renders fully (fraction bar, dot, radical, subscripts); footer "illustrative scores"; no clipping/overlap. |
| softmax-weights | 21.5–27.5 | `frame-softmax-weights.png` @ 26.6 s | PASS. 7×7 heatmap with row and rotated column token labels ("it" row label red); yellow outline on the "it" row; darkest→brightest blue encoding visible; `Σ_j w_ij = 1` renders fully; ""it" → "cat" with weight 0.75" in yellow; "rows: queries columns: keys" hint; footer "illustrative weights"; no clipping/overlap. |
| weighted-sum | 27.5–33.5 | `frame-weighted-sum.png` @ 32.8 s | PASS. Seven token-colored bars with multipliers ×0.03, ×0.75 (longest, "cat"), ×0.06, ×0.02, ×0.08, ×0.02, ×0.04 — exactly the storyboard row; arrow to a yellow-dominant output circle captioned "new vector for "it""; `out(i) = Σ_j w_ij v_j` renders fully; yellow payoff line ""it" now carries mostly "cat" — the reference is resolved"; footer "illustrative weights"; no clipping/overlap. |
| parallel-lookup | 33.5–37.5 | `frame-parallel-lookup.png` @ 36.9 s | PASS. Thin blue arcs connect token pairs strictly above the boxes without covering words; both grey captions legible including the single-head scope note; no clipping/overlap. |
| closing-formula | 37.5–42.0 | `frame-closing-formula.png` @ 41.0 s | PASS. `Attention(Q,K,V) = softmax(QKᵀ/√d) V` renders completely (upright Attention/softmax, sized parentheses, superscript ᵀ, radical over d, trailing V; no missing glyphs); italic summary line and "illustrative · silent · rendered locally" footer legible; no clipping/overlap. |
| transition 1 (title → tokens) | ~4.0 | `frame-trans1a-title-out.png` @ 3.95 s, `frame-trans1b-tokens-in.png` @ 4.15 s | PASS. End state complete and stable (no half-drawn elements); 0.15 s into the new scene the background is clean with no residual title content, scene text already readable, token boxes popping in staggered. |
| transition 2 (softmax → weighted-sum) | ~27.5 | `frame-trans2a-softmax-out.png` @ 27.40 s, `frame-trans2b-weighted-in.png` @ 27.65 s | PASS. Heatmap end state fully populated and stable; 0.15 s into the weighted-sum scene there is no heatmap residue, scene text/tag/"illustrative weights" note visible; bars have not popped in yet, which matches the design (bars begin at 0.6 s into the scene). |

Minor observation (not a defect): the small grey run-title header, scene tags, and progress bar are intentionally low-contrast furniture inherited from the template's style guide; all learner-facing primary text is white/yellow and large.

## 3. Stream and decode checks (§7.2, §7.3)

| Check | Expected | Observed | Result |
|---|---|---|---|
| Codec | h264 | `codec_name=h264` | PASS |
| Dimensions | 1280×720 | `width=1280`, `height=720` | PASS |
| Frame rate | 30/1 | `r_frame_rate=30/1` | PASS |
| Pixel format | yuv420p | `pix_fmt=yuv420p` | PASS |
| Audio streams | none | 0 audio streams | PASS |
| Duration | 42.00 s ± 1 frame + 0.01 s | `duration=42.000000`, `nb_frames=1260` | PASS |
| Full decode | empty stderr | `ffmpeg -v error -i … -f null -` → empty output, exit 0 | PASS |

Pre-render checks also passed before encoding: `--check-only` on both the installed template and the adapted copy (8 scenes, 42.00 s), `--self-test` in-memory fixture, and the adapted copy's added guard (every scene id has a handler; every scene draws cleanly at progress 0/0.25/0.5/0.75/1 without mathtext errors). The adapted copy was diffed against the template before execution: only the module docstring, the patches import, the scene-drawing section, and the pre-render guard differ; a grep for file writes, network calls, and shell execution found only the template-inherited read-only JSON loading, the `ffmpeg -encoders` preflight, and the single `animation.save` to the chosen output path.

Repair cycles used: **0** (first render passed all checks).

## 4. Runtime versions (exact, from the render environment)

- uv 0.12.21 (Homebrew 2026-09-29 aarch64-apple-darwin)
- Python 3.12.10 (uv-managed)
- numpy 2.5.3 (constraint `>=1.26,<3`)
- matplotlib 3.11.2 (constraint `>=3.8,<4`)
- jsonschema 4.26.0 (constraint `>=4,<5`)
- ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers (`/opt/homebrew/bin/ffmpeg`); encoder selected by preflight: `h264_videotoolbox`
- ffprobe from the same ffmpeg 9.0.2 build (`/opt/homebrew/bin/ffprobe`)

## 5. Reproduction

From the repository root (or from this bundle directory, since the script embeds the schema and its dependencies):

```text
uv run explainify-output/self-attention-20261002-221152/self-attention-render.py \
  --storyboard explainify-output/self-attention-20261002-221152/self-attention-storyboard.json \
  --output <new-path>.mp4
```

The output path must not already exist (the renderer refuses implicit overwrites; pass `--overwrite` only for an explicit replacement).

## 6. Limitations

- **Silent video.** This version produces no narration and no audio track, by design for v0.1.
- **Illustrative values.** All scores, weights, the 7×7 matrix, and the example vector contents are assigned for teaching, not measured from any model; this is stated in the brief and on screen.
- **Omissions** (stated in the brief and, where relevant, on screen): multi-head attention detail, training/learned projections, positional encodings, causal masking/cross-attention, layer stacking and feed-forward blocks.
- Scene inspection used 12 still frames (one representative frame per scene after key content appeared, plus two pairs around the 4.0 s and 27.5 s transitions); motion quality was assessed from the staggered/fade design and the transition states, not from playback.
- Teaching-quality checks are reviewer-confirmed accuracy, sequencing, and legibility; no user-comprehension study was performed.
