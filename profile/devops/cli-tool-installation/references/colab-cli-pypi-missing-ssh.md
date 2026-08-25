# Colab CLI — PyPI 0.6.0 Missing `ssh` + `which colab` Verification

Source: https://github.com/googlecolab/google-colab-cli/issues/102 + #102#issuecomment-5384947488 (community answer by CoffeeBEEE, not maintainer) + live probe 2026-08-24.

## Problem
- PyPI `google-colab-cli==0.6.0` has **no** `ssh` subcommand → `colab ssh --proxy-mode -s SESSION` fails with `No such command 'ssh'` when following Colab web UI instructions.
- GitHub `main` (now `src/colab_cli`, `hatch-vcs`, dep `jupyter-kernel-client = { git = "https://github.com/googlecolab/jupyter-kernel-client.git" }`) **does** have `ssh`.
- Legacy `mighty-colab v0.2.2` (today's `~/.local/bin/colab -> mighty-colab`) also has `ssh` — same binary family, different uv tool name. `uv tool list | grep colab` disambiguates.

## Verified install workaround (until PyPI >0.6.0)
```bash
export PYTHONPATH=""
uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git
# pin for repro: git+https://github.com/googlecolab/google-colab-cli.git@<sha>
which colab; readlink -f $(which colab); colab version; colab --help | grep -q ssh && echo "ssh OK"
colab ssh --help | grep -q proxy-mode && echo "proxy-mode OK"
```
Plain `pip install google-colab-cli` or `uv tool install google-colab-cli` re-installs the broken 0.6.0 — need `--force` to overwrite the cached tool. Plain `pip` may also fail on the `jupyter-kernel-client` git dep; `uv` handles it.

## Why `which colab` is the verification anchor
`colab --help | grep ssh` is meaningless without knowing *which binary* answered:
```bash
which colab                  # e.g. ~/.local/bin/colab
which -a colab               # shows shadowing (pipx vs uv vs brew shim)
ls -l $(which colab)         # e.g. colab -> mighty-colab (symlink)
readlink -f $(which colab)   # canonical: ~/.local/share/uv/tools/mighty-colab/bin/mighty-colab
                               # after git install: .../google-colab-cli/bin/colab
uv tool list | grep -E "mighty-colab|google-colab-cli"
colab version                # 0.2.2 (mighty-colab) vs 0.6.0 (PyPI)
```
Different `uv tool install` targets create different `readlink -f` paths but share `~/.local/bin/colab`. Without this chain you can test the wrong binary and misdiagnose.

## ProxyCommand / ~/.ssh/config implications
- Derive `COLAB_BIN=$(readlink -f $(which colab))` **after every** `uv tool install --force` — never hardcode `.../mighty-colab/bin/mighty-colab` or `.../google-colab-cli/bin/colab`.
- `ProxyCommand` MUST start with `/usr/bin/env PYTHONPATH=` (Hermes macOS leak: `pydantic_core._pydantic_core` ModuleNotFoundError otherwise).
- Stale `~/.ssh/config` survives reinstalls. Verify:
```bash
cat ~/.ssh/config | grep -A6 "Host colab-agent"
ssh -G colab-agent | grep -i proxycommand  # must match echo $COLAB_BIN
```
Mismatch = stale path.

## Minimal pre-flight (add to any workflow before `colab new` / `colab ssh`)
```bash
export PYTHONPATH=""
if ! colab ssh --help >/dev/null 2>&1; then
  echo "colab ssh missing — reinstalling from git..."
  uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git
  colab ssh --help | head -n 20
fi
COLAB_BIN=$(readlink -f $(which colab))
```

## Update policy
Poll `curl -s https://pypi.org/pypi/google-colab-cli/json | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['version'])"`. When `>0.6.0`, test `uv tool install --force google-colab-cli && colab ssh --help`; if `ssh` appears, PyPI can be used again.
