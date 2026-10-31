# Implementation and Verification

Use this reference only after the user approves the feasibility proposal.

## Implement the approved bridge

- Re-read the relevant files and confirm the approved scope still matches the project state.
- Follow local instructions, naming, error handling, packaging, and test conventions. Keep changes focused on the approved behavior.
- Implement the native behavior in Rust and expose it through the agreed Python-callable API. Update wrappers, exports, stubs or annotations, and affected callers as needed.
- Add or update tests for the Python-visible behavior, including relevant invalid inputs, Unicode or boundary cases, and concurrency when applicable.
- Avoid unrelated refactors and dependency additions. Ask again if a new finding changes the approved public API, bridge, dependency, compatibility, or scope.

## Build and verify

- If prerequisite setup was included in the approved proposal, perform only that authorized setup and repeat the relevant environment preflight checks before building. If setup fails or a material requirement remains unknown, report the blocker rather than attempting a build that depends on it. Approval of implementation alone does not authorize additional system changes.
- Read the project's documented build and test commands; do not assume Cargo, Maturin, `uv`, or a particular test runner is used.
- Build or reinstall the native extension after Rust changes. Confirm Python imports the newly built artifact rather than a stale shared library.
- Run the focused bridge tests and the repository checks required for the changed code. Check that Python-facing type declarations match the runtime API.
- For a performance goal, compare against the current implementation on a representative workload; report the measurement conditions and results. Do not claim speedups that the measurement does not support.
- If a required check cannot run, state why and what evidence remains unavailable.

Preflight readiness is preliminary evidence, not proof of a successful build or usable extension. Report setup, build, and fresh Python import results separately.

## Completion report

Tell the user what behavior changed, show the Python call shape or example, summarize the Rust/Python boundary changes, list checks and results, and state any unresolved limitation. Keep performance statements limited to measured or otherwise directly verified evidence.
