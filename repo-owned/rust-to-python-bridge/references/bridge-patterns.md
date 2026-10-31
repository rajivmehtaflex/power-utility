# Python and Rust Bridge Patterns

The active codebase determines the bridge. Reuse its binding mechanism and conventions when they fit the task. PyO3 with Maturin, CFFI, `ctypes`, and other approaches are options, not universal requirements. If there is no bridge, compare compatible choices in the feasibility report before creating one.

## Design the Python boundary

- Define the Python-facing function or class from the caller's needs. Keep Rust implementation details private unless the public API needs them.
- Keep runtime bindings, type stubs or annotations, documentation, and callers in sync when the public API changes.
- Choose explicit conversions for strings, bytes, collections, numeric values, and optional results. Account for conversion cost and preserve expected Python semantics.
- Map Rust failures to useful Python exceptions using the project's conventions. Define behavior for invalid inputs, empty values, Unicode, and boundary cases relevant to the task.
- Respect ownership and lifetimes at the FFI boundary. Prefer safe Rust; use `unsafe` only when required by the existing API and justify its invariants.
- Handle panics, callbacks, and Python-object access according to the selected binding framework's rules.

## Concurrency and performance

- Add parallel execution or release the GIL only when the workload and bridge permit it. Keep Python-object interaction on the side of the boundary required by the framework, and check the documentation for the versions in use.
- Establish thread-safety and object-lifetime requirements before sharing native state across calls or threads.
- Minimize copying only when the boundary supports it safely. Describe actual allocation and ownership behavior; do not call an API zero-copy based on a comment or intended design alone.
- For performance work, compare a representative workload with the current implementation and include conversion and call overhead. Report the measured environment and results without generalizing beyond the evidence.

## Choosing a bridge when none exists

Base the recommendation on supported Python versions and platforms, wheel or source distribution needs, build toolchain availability, CI/release setup, dependency policy, and whether the API needs callbacks, buffers, or complex Python objects. Prefer the smallest compatible bridge that the project can build and distribute reliably. Verify version-sensitive framework details from its primary documentation during implementation.
