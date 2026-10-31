# Discovery and Feasibility

## Inspect the project

Start from the active project root. Read applicable `AGENTS.md` and other local instructions, then inspect the narrow set of files that explain the task's data flow and conventions:

- Python entrypoints, callers, public API declarations, and type stubs.
- Rust crate roots, exported functions/classes, and any bridge or wrapper code.
- Package manifests, build scripts, dependency versions, platform and Python-version support, and CI build steps.
- Relevant tests, examples, and performance evidence.

When `.codegraph/` exists and CodeGraph is available, use it before `rg` or reading source to locate symbols and call paths. Otherwise use the repository's normal search tools. Follow existing documentation for commands and layout; never assume that one project's paths or binding library apply elsewhere.

Map the requested behavior from its Python caller through the native boundary to the Rust implementation and back. If no bridge exists, identify the repository's packaging and distribution constraints before recommending how to add one.

After identifying project requirements, perform the environment preflight linked from `SKILL.md` for every task, whether the bridge exists or must be added. Compare the actual host and selected execution environment with those requirements; inspecting manifests alone does not establish readiness.

## Evaluate feasibility

Assess the parts that can change the recommendation:

- Whether the task is a good fit for Rust and what evidence supports the expected benefit. Consider call frequency, workload size, algorithmic cost, Python/Rust conversion overhead, and maintenance cost.
- Whether the existing bridge can expose the required behavior without changing its architecture or supported platforms.
- If a bridge must be added, which options fit the project's Python versions, operating systems, build and release process, and dependency policy.
- The Python-facing signature, types crossing the boundary, ownership and allocation behavior, error mapping, Unicode and input boundaries, and concurrency or GIL requirements.
- Public API compatibility, affected callers, required tests, build steps, and acceptance criteria.

Use existing measurements or relevant project evidence when available. Do not invent benchmarks or infer speedup from the fact that code is written in Rust. If a benchmark or other experiment would materially affect the decision, propose it and describe its scope before running work that changes files or consumes substantial resources.

## Feasibility outcomes

- **Feasible:** the requested behavior fits the project and enough requirements are known to propose a concrete implementation and verification approach.
- **Conditional:** a material constraint or requirement remains unresolved; name the condition and ask only the question needed to decide.
- **Not recommended:** the bridge, workload, compatibility constraints, or lack of a credible Rust benefit makes the requested approach a poor fit. Explain why and offer alternatives without implementing one implicitly.

Report environment readiness separately from Rust suitability. Missing prerequisites or material checks that cannot be verified make the overall proposal **Conditional**, even when the workload is suitable for Rust. Include the resolution needed without treating a setup proposal as evidence that setup has succeeded.

## Feasibility report

Keep the report concise and specific to the project. Include:

1. The requested behavior and feasibility outcome.
2. The existing Python/Rust path and conventions discovered.
3. The proposed Rust responsibility and Python-callable API, including key input and error behavior.
4. Files or components likely to change, bridge or packaging needs, and compatibility concerns.
5. Main risks, performance evidence or uncertainty, and acceptance checks.
6. Environment readiness, supporting observations, missing or unverified requirements, and proposed setup commands with their required permissions and network access.
7. Any blocking question, followed by a clear request for approval of implementation and any required setup. Reuse approval already given for the same concrete scope; do not request it again without a material change.

If a requirement is underspecified, distinguish assumptions from discovered facts. Pause for the answer when it could change behavior, public API, compatibility, or implementation scope; otherwise state the narrow assumption in the report for the user to correct.
