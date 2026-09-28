# Hugging Face Generative Model Converter Skill Implementation Plan — v2

> **For agentic workers:** Use `superpowers:executing-plans` for implementation in this session, or `superpowers:subagent-driven-development` if delegated implementation is selected. Track the checkboxes below. These authoring instructions must not become dependencies of the distributed skill.

**Version:** 2.0 — 2026-09-26. Supersedes the v1 plan; incorporates the 30-point gap analysis.
**Status:** Revised implementation plan. No backend builds, model conversions, publication, or implementation tests have been performed as part of this revision.
**Goal:** Deliver an Agent Skills package in `rajivmehtaflex/power-utility` that guides a coding agent through supported text-generation and VLM conversions to GGUF, ONNX, and LiteRT-LM, with source-built tooling, real inference checks, and verified Hugging Face publication.
**Architecture:** A concise `SKILL.md` routes to concrete backend recipes. Small Python helpers handle manifests and controlled publication; they do not implement model architectures. Recipe evidence, package validation, real conversion results, and remote delivery have distinct acceptance states.
**Tech stack:** Markdown/Agent Skills; UV-managed Python environments; Git; source-built llama.cpp; Optimum ONNX with matched ONNX Runtime loading classes; `litert_torch` with LiteRT-LM; `huggingface_hub`; the official Python `skills-ref` implementation; pinned `skills` npm CLI for discovery/installation; unittest and JSON Schema checks.
**Design:** [Original scope and design](../specs/2026-09-26-hf-generative-model-conversion-skill-design.md).

## 1. Scope, corrections, and completion levels

The existing design defines the product scope. This revision specifies execution details and corrects the validator command, source-build interpretation, test methodology, and delivery omissions. The companion design now links to v2 and includes the corrected status, validator route, and LiteRT dependency caveat; P1 carries these documents into the monorepo. Additional operational details below are v2 decisions, not claims that previous execution occurred.

### Global constraints

- Primary workload: text input to generated text. Secondary: image-plus-text input to generated text for supported VLMs. Decoder-only and encoder-decoder models have separate compatibility entries.
- Targets: `gguf`, `onnx`, `litert-lm`; normalize `litert` and `litertlm` to `litert-lm`. LiteRT output is a `.litertlm` bundle.
- Resolve immutable model and tool revisions. Never silently change the requested model, target, precision, context profile, or supported workload.
- Build converter/runtime native components and their native dependencies from source during setup. Retain the user's strict default; record any explicitly authorized binary exception by component and version.
- The initial execution baseline is Linux x86_64 with CPU inference. Python 3.12 is the first compatibility candidate, not a claim that all source trees support it. P2 selects a supported Python version per backend when needed. Other operating systems and accelerators remain separate matrix entries until verified.
- Hardware-specific builds optimize the local toolchain. Record deployment restrictions separately; a host build does not establish Android, browser, mobile, or another host's artifact compatibility.
- Keep authentication local. Ask only for missing account/namespace, destination repository, visibility, and material export choices. Reuse existing user authorization and answers.
- Preserve source licenses and notices. Record the applicable terms and any supplied permission; do not treat a generic instruction to proceed as evidence that a redistribution restriction was resolved.
- Exclude fine-tuning, adapter merging/training, new architecture converters, image generation, audio/video processing, embedding/classifier tasks, quantization sweeps, and broad performance benchmarking.
- Keep model weights, build trees, secrets, private prompts, and large logs out of Git. Compile only the selected backend during ordinary skill use.
- The published skill is agent-neutral; its own operation must not require Superpowers, subagents, or a particular coding agent's tools.

### Evidence states

| State | Evidence required | Claim permitted |
|---|---|---|
| Package validated | Official metadata validator, supplemental contract checks, install/discovery evidence, behavioral scenarios | Skill package is installable; backend execution may remain unverified |
| Recipe documented | Exact commands, pins, support evidence, expected files and profile | Procedure is documented for the named tuple |
| Source build verified | Build and dependency provenance plus usable runtime | This toolchain builds on the recorded host |
| Conversion verified | Real source reference, export, target inference, staged-package reload | This model/revision/profile/backend passed the recorded checks |
| Publication verified | Authorized Hub destination, remote commit, matching file inventory/content | This exact artifact package was published successfully |
| Repository delivered | Feature branch/PR evidence; merged-commit discovery when merged | Report PR-ready, PR-open, or merged explicitly |

Each recipe also records `pending`, `passed`, `failed`, or `blocked` for each applicable check, with reasons. An upstream limitation can block one route while independent work continues. Full conversion readiness requires at least one verified text model per target and verified VLM evidence for every target advertised as VLM-verified. Package validation alone cannot close that milestone. Missing credentials or hardware leave the corresponding acceptance item pending; they never count as a pass.

## 2. Repository and file ownership

Implementation uses a durable checkout at `/root/content/power-utility`, preserving any existing checkout there. Inspect instructions/status/remotes first; use an isolated feature branch or worktree as needed. The inspected reference checkout was at `4614fe6e4cd026f4384de5a005d615623e58eb67`; fetch and record the actual implementation base before editing. `/tmp/power-utility-review` is only the previous inspection copy.

Carry this plan and its design into the monorepo's corresponding `docs/superpowers/` paths so relative references work for a fresh executor. Preserve v1 as historical documentation.

| Path relative to monorepo | Responsibility |
|---|---|
| `repo-owned/hf-generative-model-converter/SKILL.md` | Discovery, inputs, routing, phase order, stop conditions, outputs |
| `references/compatibility.md` within the skill | Supported/documented/blocked tuples, source evidence and dates |
| `references/source-builds.md` | Hardware/resource preflight, dependency policy, build and cache lifecycle |
| `references/gguf.md`, `references/onnx.md`, `references/litert-lm.md` | Executable recipes and runtime-specific package contracts |
| `references/validation.md`, `references/huggingface-upload.md` | Reference/inference checks, auth, staging, publication and recovery |
| `assets/recipes.json` | Versioned recipe records with source pins, profiles and measured status |
| `assets/manifest.schema.json`, `assets/model-card.md` | Manifest contract and destination model-card template |
| `scripts/artifact_manifest.py`, `scripts/hub_publish.py` | Deterministic file inventory/validation and controlled Hub publication |
| `tests/test_artifact_manifest.py`, `tests/test_hub_publish.py` within the skill | Meaningful helper tests with temporary files and mocked Hub calls |
| `tests/test_hf_converter_package.py` at repository root | Package links/metadata, live catalog consistency and installation portability |
| `docs/superpowers/verification/hf-converter/` | Scenario prompts/results, recipe summaries and delivery evidence; synthetic data only |
| `tools/skill-validation/pyproject.toml`, `tools/skill-validation/uv.lock` | Pinned official validator and authoring test dependencies |
| `tools/skill-validation/package.json`, `tools/skill-validation/package-lock.json` | Pinned skills installer used for acceptance |
| `README.md`, `MANIFEST.json`, `VALIDATION_REPORT.md` | Catalog entry, install example, counts and observed evidence |
| `.github/workflows/hf-generative-model-converter.yml` | Lightweight package/helper/catalog CI |
| `.github/workflows/unsloth-workflows.yml` | Narrow correction to its inherited validator installation/invocation |

Do not change generated skill collections. Update `.gitignore` only for newly introduced local environments/build/evidence directories. Reuse existing ignore rules where sufficient.

## 3. Common execution contracts

### Source-build boundary and reproducibility

| Component class | Policy |
|---|---|
| Converter/runtime code, including llama.cpp, PyTorch, ONNX, ONNX Runtime, LiteRT and native extensions used by the route | Pin sources and build native code locally; inventory transitive native libraries and build downloads |
| Python-only packages | Install pinned source distributions/checkouts; record resolved dependencies |
| Local wheels produced by this run | Allowed when provenance links them to the source build and exact configuration |
| Interpreter, compiler, linker, CMake/Ninja/Bazel, system C library, OS/GPU drivers and vendor SDK/toolkit | Declared bootstrap/system inputs; record versions and origin, without attempting to rebuild the OS or vendor drivers |
| An additional prebuilt runtime library brought in by pip, Bazel, CMake, a container, or Git LFS | Not an implicit bootstrap exception; replace through a supported source route or stop and name the dependency |

P2 produces a source/build dependency inventory before heavyweight installation. Use installer constraints and inspect build-system downloads and loaded library paths to prevent implicit binary substitution, including optional native Hub transfer extensions. Inventory licenses, versions, submodule commits, source hashes, build flags, interpreter/ABI and SDK versions. Store an exact dependency resolution per recipe, including build dependencies; do not resolve unconstrained latest dependencies during a repeat run. Recipe updates receive new revisions and repeat affected checks. Heavy builds run sequentially by default to respect the measured memory/disk budget.

Default workspace: `<user-project>/.hf-converter/`, with `sources/`, `builds/<build-key>/`, `envs/<build-key>/`, and `runs/<run-id>/{work,stage,logs}`. Reuse the supported Hub cache for checkpoint blobs. Keep local receipts beside the stage directory. `build-key` covers source/submodule revisions, dependency-lock hash, compiler/ABI, flags, target architecture and SDK versions. Incomplete builds have no ready marker. Reuse requires a matching key and runtime health check.

Inspect CPU allocation/features, effective memory limits, free writable disk, accelerator visibility, drivers and toolkits. Estimate source/build/output space and peak memory from upstream requirements or measured evidence; label unknown estimates. Cap build jobs to CPU allocation and memory headroom. If the host cannot satisfy known requirements, preserve diagnostics and stop that route. Verify the runtime's actual provider/device and report CPU fallback explicitly; source compilation alone is not evidence of acceleration.

Downloads reuse immutable revisions and resumable upstream APIs. Check shard indexes and required files before loading. Reruns reuse a verified source/build stage, but invalidate conversion and validation after changing model revision, recipe, profile, toolchain or artifact bytes. Never erase unrelated project files or healthy caches to recover a failed run.

### Inputs and recipe profiles

Capture source ID and optional requested revision, normalized target, destination details, and an optional deployment backend/profile. Inspect configuration and checkpoint layout before installing the backend. Reject unsupported adapters and source variants explicitly; never merge or dequantize them opportunistically. Require explicit selection where the repository has several viable variants. Inspect any custom-model-code requirement and record the permitted code revision/execution decision; a model ID alone is not a blanket instruction to enable arbitrary remote code.

Each recipe specifies exporter and runtime, supported architecture/task, tokenizer/template mode, precision/quantization, opset/domains where relevant, batch and sequence bounds, KV-cache/prefill settings, image processor settings, and output files. Use a documented default profile when it fits the requested deployment; otherwise ask only about the unresolved material choice. Do not claim arbitrary lengths or untested backends. Record the resolved profile, including chat-template and thinking-mode choices, before conversion.

`assets/recipes.json` has `schema_version: 1` and a `recipes` array. Each entry defines `id`, `revision`, `target`, `source`, `architecture`, `task`, `platform`, `toolchain`, `profile`, `commands`, `required_files`, `validation_policy`, `evidence`, and `limitations`. Commands identify their working directory and resolved tool; variable inputs are typed parameters. Evidence states are separate from upstream support claims. P2 fills concrete pins and thresholds before a tuple is runnable; incomplete entries are explicitly pending and never executed as if locked.

### Manifest, validation, and upload interfaces

`artifact_manifest.py` provides:

- `build_manifest(stage: Path, metadata: dict) -> dict`: inventories only approved regular files using relative paths, sizes and SHA-256; rejects paths escaping the stage and unexpected files.
- `validate_package(stage: Path, manifest: dict) -> list[str]`: checks schema, required assets, exact file set, checksums, recipe/profile identity and passed required validation gates.
- CLI: `build --stage PATH --metadata PATH --out PATH` and `verify --stage PATH --manifest PATH`.

Manifest schema version `1` contains `source`, `recipe`, `toolchain`, `build_host`, `deployment`, `profile`, `license`, `files`, and `validation`. Toolchain records include source/lock hashes and declared binary exceptions. Validation records include test fixture identifiers/hashes, generation settings, runtime/backend, phase status, limitations and numerical-check status. Exclude secrets, signed URLs and private input/output. The manifest excludes its own hash; the external publication receipt records the manifest hash and remote commit, avoiding a recursive checksum.

`hub_publish.py` provides `publish_package(stage: Path, manifest: dict, repo_id: str, *, visibility: str, create: bool, expected_head: str | None, allow_replace: bool = False) -> dict` and an equivalent CLI. Tokens come exclusively from supported local Hub configuration. The receipt contains remote repository/commit, manifest hash, file verification status and URL, never credentials.

Before expensive work, check source/gated access independently from authenticated destination identity/namespace permissions. Explain an access requirement precisely when write authorization cannot be established without attempting publication. Confirm visibility for a new repository; preserve existing visibility. Reject source-equals-destination. For existing repositories, inspect conflicts and require authorization covering replaced paths; use expected-head concurrency protection. Reuse already granted authorization instead of asking again for the same operation.

Stage only target artifacts, required processor/tokenizer/configuration files, licenses/notices, model card and sanitized evidence. Copy no entire source/build directory. Validate the immutable staged inventory immediately before upload. Use the pinned Hub client's supported resumable blob transfer and coherent commit API; verify its semantics in P6. After a lost response, inspect remote state before retrying. Report empty repos or unfinished transfers accurately. Resolve a remote commit and verify its file set and content digests; when trustworthy server digests are unavailable, stream-download to hash rather than assuming an ETag equals SHA-256. Retain the local verified package if publication fails.

License status is `clear`, `needs-evidence`, or `prohibited-under-recorded-terms`, with source references. Missing/ambiguous terms require clarification; a restriction requires an applicable alternate license or permission record before changing status. Preserve notices. The skill's own optional license field must follow an established repository license or a separately confirmed choice, not a model's license.

## 4. Review focus and verification design

The highest-risk conditions are accidental binary substitution, exporter/runtime incompatibility, publication of an incomplete package, wrong account/destination, and instructions that block valid requests. P2, P4–P7, P6, P6, and P8 respectively own those checks.

Real recipe checks use a pinned source reference and the same tokenizer/template/preprocessing settings. Start with batch 1, greedy generation, fixed seed where applicable, and at most 32 new tokens. Record a per-recipe timeout/resource budget before running. Cover three synthetic text prompts, including a near-profile-limit prompt. Require nonempty decoded output, clean termination at EOS or the configured token bound, correct format files, and no runtime errors or nonfinite values where observable.

Freeze fixture expectations before inspecting converted outputs. Source and converted models must satisfy the same simple fixture assertions. Record generated text/token comparisons. Where comparable logits or exporter parity checks exist, declare metric and threshold in the recipe before conversion and report the measured result; never relax it after failure. Quantized recipes use explicit precision-appropriate acceptance. If numerical comparison is unavailable, label numerical fidelity unverified; functional smoke evidence is not an accuracy guarantee.

For a VLM-verified claim, use a pair of controlled synthetic images with distinct expected answers and an identical prompt. First establish the reference model passes both, then require the converted pipeline to do so. Save only synthetic fixture hashes/results. Reload the final stage with source directories unavailable and model-download traffic disabled using supported settings; if OS-level network denial is not exercised, state that limitation. Verify local file access paths to detect dependence on original weights or hidden model caches.

Behavioral scenarios use fixed prompts/rubrics and fresh contexts. Preserve successful no-skill baselines; do not intensify prompts until they fail. Include successful conversions, aliases, credential reuse, licensed publication, explicit component-level exceptions, and blocked paths. A skill that refuses all requests fails. Record harness/model identity, skill revision, inputs, decisions and evidence. Run one baseline and one guided sample per scenario; for the two critical source-build/publication rules, use five samples per condition. Allow one targeted revision/retest round; report residual inconsistency instead of looping indefinitely. Only real conversion checks establish tool execution.

## 5. Implementation sequence

### P1 — Establish the durable branch and correct validation tooling

**Files:** Carry design/v1/v2 into `docs/superpowers/`; create `tools/skill-validation/{pyproject.toml,uv.lock,package.json,package-lock.json}`; narrowly modify `.github/workflows/unsloth-workflows.yml`; record `docs/superpowers/verification/hf-converter/baseline.md`.
**Consumes:** This plan, repo instructions and current remote state. **Produces:** recorded base commit and reproducible authoring tools.

- [ ] Inspect the durable checkout and current remote default branch; preserve user changes and create the feature branch `feat/hf-generative-model-converter` with isolation appropriate to the session. Record the actual base SHA.
- [ ] Carry the documents into the monorepo; mark v1 superseded. Update the carried design's status to scope approved/v2 details pending execution, correct its validator route, and explain the LiteRT transitive-binary gate.
- [ ] Install the official `agentskills/agentskills` Python validator from a verified immutable revision/subdirectory in the UV project. Lock its dependencies. Pin the skills installer separately in `package-lock.json`; record versions and supported local-list/install commands.
- [ ] Run the existing root and Unsloth tests and official validator on the existing owned skill; record any pre-existing failures. Correct only the inherited npm-validator invocation/setup in the Unsloth workflow and its documented command. Do not rewrite unrelated workflow behavior.
- [ ] Verify `uv run --project tools/skill-validation skills-ref validate repo-owned/unsloth-workflows` runs the pinned official tool. Record that this checks frontmatter/naming, not links or runtime behavior. Commit the isolated tooling/document correction when healthy.

### P2 — Resolve source-build feasibility, compatibility, and pins

**Files:** Create `references/compatibility.md`, `references/source-builds.md`, `assets/recipes.json`; record `docs/superpowers/verification/hf-converter/feasibility.md` and recipe-specific dependency-lock evidence.
**Consumes:** P1 tools and hardware metadata. **Produces:** explicit exporter/runtime pairs, dependency inventories, immutable pins and resolved profiles; unknown support cannot advance as supported.

- [ ] Inspect the host and inventory direct/transitive native components for each backend using official build manifests. Check LiteRT's fetched/prelinked libraries explicitly. A source build of one executable cannot close this dependency audit.
- [ ] Seed the matrix below as candidates only. Verify architecture registries, model files/licenses/access and exact platform support, then resolve immutable checkpoint/tool revisions. A sample change is recorded as a new test case; ordinary user runs never substitute their requested source model.

| Workload candidate | GGUF route | ONNX route | LiteRT-LM route | Initial status |
|---|---|---|---|---|
| `Qwen/Qwen3-0.6B`, decoder-only | llama.cpp HF converter + matching generation CLI | Optimum ONNX + `ORTModelForCausalLM`, if supported at resolved revisions | `litert_torch` Qwen3 export + LiteRT-LM runtime | Pending support/build checks |
| `HuggingFaceTB/SmolVLM-256M-Instruct`, VLM | Multimodal converter/runtime pair if supported | Deferred (2026-09-28 decision): out of scope for now | No assumed route | GGUF verified; ONNX deferred; unclaimed for LiteRT |
| `google/gemma-3-4b-it`, VLM | Alternative evidence row only if needed | Alternative evidence row only if needed | Candidate only after exporter/runtime, access and resource checks | Pending; no automatic download |
| Encoder-decoder families such as T5 | Check upstream support; no promise | Separate seq2seq exporter and `ORTModelForSeq2SeqLM` route | Check upstream support; no promise | Documented-only until a specific recipe is verified |

> Scope update (2026-09-28): the ONNX route is **text-generation only** for now. The SmolVLM ONNX tuple is deferred — it stays recorded as out of scope/deferred in `assets/recipes.json`, is never attempted during the ONNX round, and ONNX must not be advertised as VLM-verified. The GGUF route retains both verified tuples.

- [ ] For each accepted tuple, resolve and freeze interpreter, source/submodule revisions, build tools, runtime/exporter packages and native dependency locks. Verify prerequisites without installing heavyweight packages yet. Save exact commands, flags, files, profile and failure conditions; shared pseudocode is insufficient.
- [ ] Define resource estimates, parallelism cap, runtime budget, build key and ready marker. Decide host and deployment backend separately. Record compatible binaries needed from outside the build; block undeclared runtime binaries and continue independent routes.
- [ ] Populate recipe evidence as documented/pending/blocked without invented versions or success. Do not mark the recipe locked until it contains all concrete values. Review feasibility before spending effort on large builds.

### P3 — Specify scenarios and author the common skill workflow

**Files:** Create `SKILL.md`, `references/validation.md`, `references/huggingface-upload.md`, `assets/model-card.md`; create `docs/superpowers/verification/hf-converter/scenarios.md` and `behavior-results.json`.
**Consumes:** P2 support decisions and execution contracts. **Produces:** portable shared instructions and fixed behavioral oracles.

- [ ] Write scenario inputs and pass/fail rubrics before authoring guidance. Include five failure scenarios: unsupported model/target, hidden prebuilt dependency, unresolved license, credential disclosure, and target-inference failure despite an output file. Include positive text/VLM paths, aliases, existing auth, authorized exceptions, and destination conflicts.
- [ ] Run and record no-skill baselines with fresh-context agents. Preserve passes as regression controls; use actual observed failures to refine guidance. No scenario performs network writes or uses real secrets.
- [ ] Write `name: hf-generative-model-converter`; description starts `Use when...` and explains capability and triggers concisely, within 1,024 characters. Add the specific environment/network requirements in `compatibility` within 500 characters. Use string metadata values, a known skill license only, and fewer than 500 body lines.
- [ ] Implement the shared phase order and phase-result reporting; link every reference directly from `SKILL.md`. Include source policy, profile selection, access/license gates, staging, helpers, positive worked invocation, and explicit out-of-scope handling. Use generic coding-agent language and commands relative to the installed skill directory.
- [ ] Review the resulting instructions against all common contracts; keep guidance proportional to observed risks instead of adding an ever-growing prohibition list.

### P4 — Produce the GGUF recipe and verify its source build

**Files:** Create `references/gguf.md`; update GGUF records in `assets/recipes.json` and local build evidence.
**Consumes:** P2 pins/inventory/profile. **Produces:** exact GGUF conversion/runtime commands and a build result.

- [ ] Write commands for pinned source retrieval, isolated Python converter dependencies and CMake native builds. Include a matching runtime executable and explicit hardware backend/flags.
- [ ] Specify supported weight conversion and quantization choices, tokenizer/template preservation, required VLM projector files and exact expected output inventory.
- [ ] Build the accepted CPU tuple from source within its recorded resource budget. Inspect dependency provenance and runtime health. Verify optional accelerator use only on an available supported device; otherwise leave it unverified.
- [ ] Record executable paths/hashes, versions and flags. Build failure retains logs and blocks execution verification for that tuple; it does not cause a prebuilt substitution. P7 performs model-level acceptance.

### P5 — Produce ONNX and LiteRT-LM recipes and verify builds

**Files:** Create `references/onnx.md`, `references/litert-lm.md`; update corresponding recipe and local build evidence.
**Consumes:** P2 exporter/runtime pairs. **Produces:** concrete procedures and source-build outcomes per backend.

- [ ] For ONNX, choose the matched Optimum exporter/loading class per workload. Treat ONNX Runtime GenAI as a separate recipe requiring its own supported graph layout, configuration and source build; never use it as a drop-in loader for an arbitrary Optimum output. **Scope (2026-09-28):** ONNX covers text-generation only (`Qwen3-0.6B` → `ORTModelForCausalLM`); the VLM ONNX tuple is deferred and recorded as out of scope, not attempted.
- [ ] Specify source builds of exporter-side native dependencies and ONNX Runtime, including compatible execution-provider SDKs, checker version, opset/domains, cache graphs, external-data filenames, processor/tokenizer/configuration files and the generation command.
- [ ] For LiteRT-LM, specify the exact source-built exporter/runtime pair, bundle metadata/template/image assets, profile/cache settings and supported quantization recipe. Audit prebuilt libraries fetched by the build system; either establish a supported replacement from source or record the named blocker.
- [ ] Execute independent accepted source builds with locked dependencies and runtime health checks. Capture active provider and loaded-library provenance. Keep failures scoped to their tuple; P7 performs model-level acceptance.

### P6 — Implement manifests and publication with meaningful tests

**Files:** Create `assets/manifest.schema.json`, `scripts/artifact_manifest.py`, `scripts/hub_publish.py`, `scripts/pyproject.toml`, `scripts/uv.lock`, `tests/test_artifact_manifest.py`, `tests/test_hub_publish.py` within the skill.
**Consumes:** Common interfaces and recipe/package contracts. **Produces:** deterministic staging verification and recoverable Hub publication.

- [ ] Write failing temporary-file tests for exact inventories, missing sidecars, altered hashes, escaping/symlink paths, unexpected source weights, forbidden secret fields, schema/status failures, and the nonrecursive manifest/receipt relationship.
- [ ] Implement `build_manifest` and `validate_package` plus their CLIs. Validate against the versioned schema; error messages identify a file or phase without leaking private values. Run the focused tests to pass.
- [ ] Write mocked-Hub tests for missing source/destination access, wrong namespace, visibility mismatch, same source/destination, file conflicts, stale expected head, failed inference, interrupted transfer, lost commit response, repeat publication and remote mismatch. Assert no write calls before prerequisites pass.
- [ ] Verify current pinned Hub APIs for resumable transfer, expected-parent commits and remote digest retrieval; implement `publish_package`. Use a local receipt outside the staged inventory. Hash streamed remote bytes when no reliable digest is available. Run focused tests to pass.
- [ ] Verify paths containing spaces and invocation from outside the skill/project directory. Record dependency provenance for the helpers under the same binary policy when used during conversion. Commit the helpers and recipe documents after focused checks.

### P7 — Run actual model conversion and package acceptance

**Files:** Update `assets/recipes.json`, `references/compatibility.md`; create `docs/superpowers/verification/hf-converter/runtime-results.json` and `runtime-summary.md`. Large artifacts/logs stay in the ignored workspace.
**Consumes:** Healthy source-built toolchains, staged-package helpers and pinned test models. **Produces:** real evidence per model/profile/runtime tuple.

- [ ] Resolve source access/license and resource requirements before downloading each selected checkpoint. Load a native reference with recorded preprocessing/template/settings; freeze fixtures, expectations, tolerances and timeout before evaluating converted outputs.
- [ ] Execute the exact documented commands for each feasible text target, check its format/package, run bounded target inference and compare against the reference as described in section 4. Record elapsed build/conversion/inference phases without presenting them as a performance benchmark.
- [ ] Execute VLM checks only for tuples advertised for verification; use the two-image test. Unsupported or inaccessible combinations retain explicit pending/blocked status. No replacement of a VLM check with text-only inference.
- [ ] Stage the complete package and reload with original source paths unavailable. Check file-access evidence and model-download restrictions. Re-run after any artifact/profile/toolchain changes; record smoke and numerical-fidelity states separately.
- [ ] With an explicitly supplied authorized test namespace/repository, perform a real Hub publication and remote content verification. Prefer a new private test repository with selected visibility; do not invent an account or automatically delete it afterward. If credentials/destination are unavailable, finish local checks and leave live-publication acceptance pending.
- [ ] Classify every recipe using observed results. At least one verified text recipe per target is required for the full three-target readiness claim. Document a precise source-build limitation instead of disguising partial coverage.

### P8 — Test agent behavior and installation portability

**Files:** Update scenario/results evidence; create root `tests/test_hf_converter_package.py`; refine affected skill/reference files.
**Consumes:** Authored skill and fixed scenarios. **Produces:** behavioral evidence and portable package checks.

- [ ] Run guided scenarios under the fixed rubric/budget in section 4. All publication/credential/build boundaries must hold, and valid requests must reach the correct next action. Record control and guided results, including residual failures.
- [ ] Add supplemental package checks for direct relative links, copied-file availability, allowed frontmatter, metadata string values, description/compatibility limits, main-file line budget, and internal recipe/schema consistency. Check semantic properties rather than requiring exact prose phrases.
- [ ] Use the pinned installer to list and install the local skill into two disposable agent layouts when supported. Verify copied references/helpers resolve from an unrelated working directory and run helper `--help`/fixture validation. Do not modify the user's actual global skills directories.
- [ ] Exercise read/route/use behavior in two different coding-agent hosts when available. If only one host is available, report single-host behavior plus static/install portability evidence; do not claim universal agent compatibility.
- [ ] Allow one focused correction/retest round for observed failures; report any remaining failures before claiming package validation. Source-build and inference evidence remains owned by P4–P7.

### P9 — Integrate catalog, CI and generated-refresh durability

**Files:** Modify root `README.md`, `MANIFEST.json`, `VALIDATION_REPORT.md`; create `.github/workflows/hf-generative-model-converter.yml`; extend `tests/test_hf_converter_package.py` as needed. Narrow changes to `tools/import_generated_skills.py` and its tests are permitted only if refresh loses or falsifies this entry's evidence.
**Consumes:** Actual validation/evidence. **Produces:** consistent catalog and reproducible lightweight CI.

- [ ] Add one README index row, install example and runtime limitations; add one matching manifest entry with `source: repo-owned` and the correct destination. Distinguish skill license from model licenses. Derive compliance/warnings from observed package checks.
- [ ] Add semantic checks for unique name/destination, existing path, description/metadata consistency, one index row, displayed totals and validation-report evidence. Allow ordinary mentions in installation examples. Preserve pre-existing warnings and label historical validation scope.
- [ ] Exercise a generated refresh on a disposable fixture/copy containing the new owned skill; confirm files and metadata survive. The current importer assigns compliance optimistically, so ensure refresh never upgrades failed/unknown evidence to passed. Make only a demonstrated, tested correction if needed.
- [ ] Configure CI with pinned authoring dependencies/actions, explicit supported Python/Node versions, read-only permissions, and path triggers covering the skill, helper tests, validator tools/locks, catalog and workflows. Run official metadata validation, supplemental checks, helper tests and existing importer tests. Keep model downloads, source builds and live Hub writes out of routine CI.
- [ ] Recheck the existing Unsloth workflow because catalog edits trigger it. Record unrelated baseline failures accurately; do not mark checks passed on the strength of valid JSON alone.

### P10 — Review and deliver through GitHub

**Files:** Finalize `docs/superpowers/verification/hf-converter/delivery.md` and evidence summaries; review the complete feature branch.
**Consumes:** P1–P9 outputs and available GitHub authorization. **Produces:** reviewable branch/PR and an explicit delivery state.

- [ ] Run the focused checks below and inspect the complete diff. Confirm all runtime claims match recipe evidence, credentials/weights are absent, docs travel with the branch, and scope remains limited to this skill plus demonstrated tooling/integration fixes.
- [ ] Commit reviewable groups on the feature branch and record the commit IDs. Recheck the remote base for conflicts before opening a PR; rerun affected checks after conflict resolution.
- [ ] When repository access permits, push the feature branch and create a draft PR to `rajivmehtaflex/power-utility`, including verified/pending/blocked backend and publication states. If access is unavailable, preserve the local branch and report the exact remaining access requirement.
- [ ] Follow required repository checks/review. Merge only with applicable authorization; a PR is a separate delivery state from merged inclusion. Do not report the remote default branch as updated before it is.
- [ ] Verify discovery/installation from the pushed branch/commit using the pinned CLI's documented ref syntax. After merge, verify the normal `rajivmehtaflex/power-utility` install/list command against the merged revision and record its identity.

## 6. Acceptance commands and release rules

Run from the monorepo root after P1 provisions tools. Additional dependencies used by these commands must be locked in the authoring environment.

```bash
uv sync --project tools/skill-validation --locked
uv run --project tools/skill-validation skills-ref validate repo-owned/hf-generative-model-converter
uv run --project tools/skill-validation python -m unittest discover -s repo-owned/hf-generative-model-converter/tests -v
uv run --project tools/skill-validation python -m unittest discover -s tests -v
uv run --project tools/skill-validation python -m json.tool MANIFEST.json
npm ci --prefix tools/skill-validation
git diff --check
```

P1 records the exact pinned installer invocation for local and remote list/install checks; invoke its installed executable without permitting `npx` to fetch an unpinned replacement. A metadata validator success does not replace supplemental or runtime checks.

Package release requires metadata/link/schema/helper/catalog checks, bounded behavioral evidence and a truthful compatibility matrix. Conversion readiness additionally requires the P7 real-model results. Live upload readiness requires an authorized real publication with remote verification. GitHub delivery reports local branch, PR-open, or merged state separately. Any outstanding target, access, platform or fidelity limitation remains visible in the model/skill documentation and completion report.

## 7. Gap-to-task coverage

This table maps the previous review's identifiers to planned work. It records remediation coverage, not completed implementation.

| Gap | Resolution owner and evidence |
|---|---|
| 01 — Validator installation | P1: pinned official Python validator; inherited workflow corrected |
| 02 — LiteRT prebuilt dependencies | P2/P5: dependency audit and explicit source-build feasibility result |
| 03 — Source-build boundary | Section 3/P2: component classifications, provenance and exceptions |
| 04 — No actual conversion acceptance | P7: real text/VLM runs and explicit readiness states |
| 05 — Compatibility matrix | P2: seeded candidates, separate architecture/platform/status rows |
| 06 — ONNX pairing | P2/P5: matched exporter/runtime/graph-package recipes |
| 07 — Reproducible recipes | P2/P4/P5: concrete pins, commands, files and expected failures |
| 08 — Dependency locks | P1/P2: authoring and per-recipe build/runtime resolutions |
| 09 — Execution baseline | Section 1/P2: Linux x86_64 CPU baseline; other tuples separately verified |
| 10 — Build versus deployment hardware | Sections 1/3, P2/P7: distinct host/deployment records |
| 11 — Resource checks | Section 3/P2/P4/P5: estimates, effective limits, jobs and provider evidence |
| 12 — Environment/cache lifecycle | Section 3/P2: explicit layout, build key and readiness checks |
| 13 — Download/restart behavior | Section 3/P6/P7: immutable reuse, shard checks and invalidation |
| 14 — Nonstandard checkpoints | Section 3/P2/P3: variants, adapters, quantized sources and custom code |
| 15 — Export profiles | Section 3/P2: resolved cache/context/image/precision settings |
| 16 — Source and destination access | Section 3/P6: distinct checks and actionable access results |
| 17 — Existing destinations | Section 3/P6: conflicts, visibility, source identity and expected head |
| 18 — Upload file set | Section 3/P6: isolated stage, allowlist and hash validation |
| 19 — Upload recovery/completion | Section 3/P6/P7: resumable transfer, reconciliation and remote receipt |
| 20 — Manifest contract | Section 3/P6: schema v1, tests, evidence states and no self-hash cycle |
| 21 — License resolution | Section 3/P3/P6: evidence-based status and separate skill license |
| 22 — Inference success | Section 4/P7: bounded source/target fixtures and explicit fidelity status |
| 23 — Package independence | Section 4/P7: staged reload without source/cache-model dependence |
| 24 — Forced failing baselines | Section 4/P3/P8: retained passing controls and bounded evaluation |
| 25 — Positive behavior coverage | P3/P8: success, aliases, auth reuse and authorized exception cases |
| 26 — Scenario reproducibility | Section 4/P8: fixed rubric, identities, samples and iteration budget |
| 27 — Validator scope/metadata | P1/P3/P8: official metadata check plus explicit supplemental checks |
| 28 — Integration evidence | P8/P9: disposable installation, catalog semantics and refresh durability |
| 29 — Durable handoff | P1: durable checkout, actual base SHA and carried design/plan |
| 30 — GitHub delivery | P10: commits, branch/PR, authorization-aware merge and remote discovery |

## 8. Authoritative starting references

Recheck these against the selected immutable revisions during P1–P5; the links establish provenance, not compatibility for every model.

- [Agent Skills specification](https://agentskills.io/specification) and [official Python validator](https://github.com/agentskills/agentskills/tree/main/skills-ref).
- [skills installer](https://github.com/vercel-labs/skills) and [power-utility repository](https://github.com/rajivmehtaflex/power-utility).
- [llama.cpp source builds](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md) and [multimodal runtime](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md).
- [Optimum ONNX export/inference](https://huggingface.co/docs/optimum-onnx/quickstart), [runtime classes](https://huggingface.co/docs/optimum-onnx/onnxruntime/package_reference/modeling), [ONNX Runtime builds](https://onnxruntime.ai/docs/build/), and [GenAI model preparation](https://onnxruntime.ai/docs/genai/howto/build-model.html).
- [LiteRT-LM source-build guide](https://github.com/google-ai-edge/LiteRT-LM/blob/main/docs/getting-started/build-and-run.md), [LiteRT Torch](https://github.com/google-ai-edge/litert-torch), and [Qwen3 bundle recipe](https://github.com/google-ai-edge/LiteRT-LM/blob/main/models/qwen3/README.md).
- Candidate source cards: [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), [SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct), and [Gemma 3 4B](https://huggingface.co/google/gemma-3-4b-it). None is marked locally verified by this plan.
