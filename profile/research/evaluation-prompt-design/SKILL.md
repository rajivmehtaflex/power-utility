---
name: evaluation-prompt-design
description: Design, categorize, refine, and publish structured test prompts for comparing AI models (MoA vs closed-source, frontier vs open, etc.). Covers physics simulation prompts, complex SVG/art prompts, code generation prompts, and multi-turn corrections.
license: MIT
metadata:
  author: Hermes Agent
  hermes_category: research
  hermes_related_skills: get-info, svg-illustration, github-issues, github-repo-management
  hermes_tags: evaluation, benchmarking, prompt-engineering, svg, gist, moa, model-comparison
  title: Model Evaluation Prompt Design
  version: 1.0.0
---

# Evaluation Prompt Design

Design structured, multi-category test prompts for model benchmarking, with user-driven refinement and gist-based publication.

## When to Use

- User asks for test prompts to compare models (MoA vs closed-source, frontier vs distilled, etc.)
- User wants prompts categorized by capability axis (physics, SVG, code, reasoning, etc.)
- User wants multiple batches with progressive refinement
- User wants finalized prompts published as a gist or shared artifact

## Workflow

### Step 1 — Understand the Test Axis

Determine what capability the user wants to evaluate. Common axes:

| Axis | What to generate | Example from this session |
|------|------------------|---------------------------|
| Physics simulation | Interactive browser code (HTML + CSS + JS + WebGPU) | Particle collision, N-body gravity, spring-mass, fluid, rigid body |
| SVG art generation | Complex SVG illustration prompts | Botanical mandala, futuristic city, biomechanical dragon, mechanical orrery |
| Code generation | Programming task prompts | Single-file WebGPU demos, physics engines |
| Multi-modal / layout | Structured composition from natural language | Dashboards, posters, cross-section diagrams |

### Step 2 — Generate Prompt Batches

Always produce **batches of 5** prompts unless the user specifies otherwise.

Each prompt should be:
- **Short and actionable** — a single paragraph the evaluator can paste as-is
- **Self-contained** — includes format constraints (e.g., "pure SVG only, no HTML wrapper, no raster")
- **Scoped to the test axis** — physics prompts mention energy/momentum metrics; SVG prompts mention viewBox, gradients, masks, groups

### Step 3 — Handle User Corrections

The user may reject or refine a batch. Common correction patterns:

| Correction signal | Response |
|---|---|
| "Don't make X the subject" | Remove the test target from the *content* of the prompt itself. The prompt should describe an independent subject (engineering diagram, nature scene, scientific poster) that stresses the model — not the model itself. |
| "More complex" | Add more SVG features (masks, filters, symbols, clip paths), more structural layers, physics-aware constraints (tension, pressure, load), and larger viewBox. |
| "Harder" | Increase density of elements, add coordinate precision requirements, require reusable components via `<defs>` and `<symbol>`, add labeling/annotation sub-tasks. |

### Step 4 — Categorize

After generating all batches, organize them into a table with:

| Column | Content |
|--------|---------|
| # | Number within category |
| Category | Name (e.g., "Physics + Browser Tests", "Complex SVG Illustration") |
| Prompt Name | Short title |
| Description | 1-sentence summary of what the prompt tests |

If the user asks for a refined version of a category (e.g., "ultra-complex" after "complex"), create a new table row beneath the original and note the refinement relationship.

### Step 5 — Publish as Gist

When the user asks to publish:

```bash
# Write markdown file locally
write_file(path="/Users/rajivmehtapy/<filename>.md", content="...")

# Create public gist
gh gist create <path> --desc "<descriptive title>" --public

# Clean up local temp file
rm <path>
```

Use `--public` unless the user specifies otherwise. The gist URL is printed on creation — share it with the user.

## Pitfalls

1. **Don't make the test target the subject of the prompt.** A prompt that says "draw a MoA system" tests the model's knowledge of MoA, not its SVG generation ability. The subject should be independent (e.g., "biomechanical elephant," "space elevator," "fusion reactor cross-section").

2. **Don't stop after one batch.** The user expects refinement — ask whether they want more complexity, a different axis, or a completely different category before declaring done.

3. **Don't skip categorization.** A flat list of 15+ prompts without grouping is hard to use in a benchmark. Always organize into meaningful category tables.

4. **Don't embed assumptions about side-effects in prompts.** Avoid phrasing like "generate and render" for SVG prompts — pure generation is the test; rendering is the user's concern.

5. **Don't forget to delete the temp file after gist creation.** The markdown file was already published; keeping it is clutter.

## Verification Checklist

- [ ] Prompts are short, self-contained, and pasteable
- [ ] Each batch is 5 prompts (unless user specified otherwise)
- [ ] Categories are clearly separated in output
- [ ] Corrections from user are incorporated before finalizing
- [ ] Gist is created with `--public` flag
- [ ] Local temp file is cleaned up after publication
