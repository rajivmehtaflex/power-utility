# Remote Bootstrap and Local Launcher Workflow

Use this reference when a remote bootstrap script must leave a tool runnable with an exact command such as `./code tunnel` after the bootstrap shell exits.

## Contract first

Define the postcondition before editing the installer:

```text
Working directory: /content
Bootstrap: curl -fsSL <stable-raw-url> | bash
Required follow-up: ./code tunnel
```

This contract means the installer must create `/content/code`. Installing only to `/usr/local/bin/code` or `$HOME/.local/bin/code` is insufficient, even if the installer can run `code --version` internally.

## Why PATH-only installs fail with `curl | bash`

The pipeline starts a child Bash process. An `export PATH=...` performed inside that child is not propagated back to the shell that launched `curl | bash`. Therefore:

- `code` may work during installer verification;
- `code` may not work in the caller's next command;
- `./code` can work only if a file named `code` was placed in the caller's current directory.

Do not claim that a PATH export solves a relative-path requirement.

## Implementation pattern

1. Resolve the physical current directory with `pwd -P`.
2. Require it to be writable when the contract requires `./code`.
3. Set `CODE_BIN="$CODE_WORKDIR/code"`.
4. Map architecture to the vendor's current artifact names. For the VS Code standalone CLI, validate `cli-alpine-x64` and `cli-alpine-arm64`; stale `cli-linux-x64` links may return 404.
5. Download into a temporary directory with `curl --fail --location`.
6. Extract and require an executable named `code`.
7. Install into a temporary file beside the final target:

```bash
staged_code="$(mktemp "${CODE_BIN}.tmp.XXXXXX")"
install -m 0755 "$extract_dir/code" "$staged_code"
mv -f "$staged_code" "$CODE_BIN"
```

8. Verify the exact target:

```bash
"$CODE_BIN" --version
"$CODE_BIN" tunnel --help
```

9. Print the exact user command from that directory:

```text
./code tunnel
```

Do not rely on `command -v code` as the final check when the required contract is a local executable. A pre-existing global `code` command can mask a missing local launcher.

## Piped-script guard

With `set -u`, this direct-execution guard fails when the script is read from stdin because `BASH_SOURCE[0]` can be unset:

```bash
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
```

Use a defaulted expansion and allow stdin execution:

```bash
if [[ -z "${BASH_SOURCE[0]:-}" || "${BASH_SOURCE[0]:-}" == "$0" ]]; then
  main "$@"
fi
```

Test both forms:

```bash
bash tunnel_ext.sh --help
cat tunnel_ext.sh | bash -s -- --help
```

## Gist publication and verification

For a requested account and existing Gist:

```bash
gh auth switch --user <requested-account>
test "$(gh api user --jq '.login')" = "<requested-account>"
gh gist edit <gist-id> --filename tunnel_ext.sh tunnel_ext.sh
```

After editing:

1. Read the Gist API metadata to obtain the new revision raw URL.
2. Fetch both the revision URL and the stable raw URL.
3. Compare each fetched file with the tested local file using `cmp -s`.
4. Run `bash -n` and ShellCheck against the fetched file.
5. Run the piped `--help` check against the fetched file.
6. Tell users to use the stable raw URL; a previously copied immutable revision URL will continue serving old code.

Never expose authentication output or tokens.

## Verification matrix

| Check | Purpose |
|---|---|
| `bash -n` | Syntax correctness |
| ShellCheck | Static shell correctness |
| Fake archive fixture | Proves the exact `./code` placement without needing Linux runtime |
| `bash -s -- --help` | Proves stdin/pipeline execution |
| `--version` and `tunnel --help` on `$CODE_BIN` | Proves the installed executable, not a PATH fallback |
| Current vendor endpoint checks | Detects stale documentation URLs |
| Remote `cmp` against local | Proves the published Gist is the tested artifact |

A macOS host can validate extraction, placement, syntax, and endpoint behavior, but it cannot execute a Linux CLI binary. Report the missing Linux runtime smoke test instead of fabricating it.
