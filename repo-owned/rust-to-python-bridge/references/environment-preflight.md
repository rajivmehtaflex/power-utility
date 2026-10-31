# Environment Preflight

Run this read-only assessment after discovering project requirements and before presenting the feasibility proposal. It applies to existing and new bridges, including on plain headless Ubuntu. A terminal is sufficient; no GUI, Python interpreter, Rust installation, package manager, or administrator access is assumed to exist.

## Establish the requirements

Derive the required Python and Rust versions, target architecture, bridge/backend, system dependencies, and build commands from project instructions, manifests, toolchain files, and CI. Distinguish the build host from the deployment target if they differ. Check the environment that will actually run the build and Python caller, including a documented container or remote environment when applicable; do not substitute facts about another host.

Check only relevant dependencies. PyO3/Maturin, CFFI, and `ctypes` projects can have different needs. Do not require Maturin, `uv`, Python headers, or a Rust compiler on the runtime host when the project's build/distribution path does not require them. If a requirement is unknown, record that uncertainty instead of inventing a version or package.

## Inspect without changing setup

- **Host and resources:** identify OS/version and CPU architecture. On Linux, read `/etc/os-release` when available and inspect kernel/architecture information. Check available disk space for the project/build location and memory limits, including container limits when applicable. Without a documented or measured minimum, report observations rather than declaring resources sufficient.
- **Python:** locate the intended interpreter and virtual environment, record its executable path and version, and compare them with project requirements. Detect a selected interpreter outside the intended environment. Check headers or development libraries only where the backend needs them; use interpreter configuration or installed-package metadata without importing project code.
- **Rust:** inspect the project's pinned toolchain and target requirements, installed toolchains, executable paths, and versions. Distinguish an installed compiler from a rustup shim. Do not invoke a shim in a way that can install a missing pinned toolchain. Use installed-toolchain metadata or an identified installed compiler binary; otherwise report the version as unverified.
- **Native dependencies:** inspect the required compiler, linker, libraries, and discovery tools such as `pkg-config` only where relevant. Use known read-only metadata/version queries; do not compile test programs or run project build scripts during preflight.
- **Build tools:** check the actual packaging/build tools and their versions in the selected environment. A tool missing from the current shell may be installed elsewhere or intentionally isolated by the backend. Distinguish unavailable, installed but inaccessible, incompatible, and not applicable; a failed lookup alone proves only that the current lookup did not find it.
- **Access:** inspect relevant directory permissions and discover available installation routes without changing files or escalating privileges. Do not assume `sudo` exists or attempt a password prompt. Do not dump environment variables or credentials. Record network restrictions supplied by the user or project; network reachability remains unverified unless an authorized check establishes it. An offline host can still be viable with suitable cached dependencies or prebuilt artifacts.

Use shell built-ins first and guard optional commands. For example, this fragment discovers common executable paths on Ubuntu without requiring them to be installed:

```sh
if [ -r /etc/os-release ]; then
    cat /etc/os-release
fi
for tool in python3 rustup rustc cargo cc pkg-config; do
    if command -v "$tool" >/dev/null 2>&1; then
        command -v "$tool"
    else
        printf '%s: unavailable on current PATH\n' "$tool"
    fi
done
```

This fragment is a starting point, not a readiness verdict. Use OS-appropriate alternatives elsewhere. Check whether each further command can run without side effects before using it: even version commands through tool managers may bootstrap downloads. For Python introspection, use isolated startup with site loading and bytecode writes disabled where supported, and inspect standard-library configuration rather than importing the application.

Do not install packages, refresh package indexes, create or activate environments, change `PATH`, run generators/builds, or make network requests just to complete preflight. If a necessary diagnostic would mutate setup, require downloads, or lack available tooling, record it as unverified and propose the next step.

## Report readiness and remediation

Present a compact table with each relevant requirement, observed path/version or other evidence, and its result. Mark irrelevant checks **Not applicable**. Give the environment one overall result:

- **Ready:** applicable prerequisites are supported by observations and no material readiness check remains unresolved. State any unverified nonblocking conditions, including network availability when no download is needed.
- **Missing prerequisites:** a required tool, compatible version, library, resource, or access route is demonstrably missing or unusable. List any additional unverified checks alongside the known blockers.
- **Unable to verify:** no definite missing prerequisite has been established, but a material requirement or observation is unavailable. Name what evidence is needed.

Include proposed terminal-only setup commands for known gaps, tailored to the detected OS/version, architecture, project toolchain, and installation policy. On Ubuntu, use appropriate Ubuntu package names only after confirming applicability; do not copy Ubuntu commands to another OS. Prefer the project's existing environment/toolchain management. State which commands need administrator access or network access, and offer an applicable user-local or offline route when available. Do not present an unverified workaround as certain to work.

For example: `Missing prerequisites — the project pins Rust 1.85, but the installed-toolchain inventory contains only 1.84. Installing the project-pinned toolchain needs approval and network access; network reachability is unverified. Python checks passed; the build has not been attempted.`

Include setup in the existing feasibility approval proposal instead of adding a separate approval loop. Existing approval of the same setup scope remains valid. After authorized setup, repeat the affected checks before building. A **Ready** preflight does not replace the later native build, focused tests, or fresh Python import verification.
