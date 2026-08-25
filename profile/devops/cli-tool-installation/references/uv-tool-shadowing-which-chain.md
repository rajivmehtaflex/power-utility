# `uv tool` Shadowing — Same Shim from Multiple Tools

**Class:** When two `uv tool` installs expose the same command (e.g. `mighty-colab` vs `google-colab-cli` both provide `colab`), `colab --help | grep ssh` is meaningless without identifying *which binary* answered.

## Why

`uv tool install <tool>` creates `~/.local/bin/<shim>` → `~/.local/share/uv/tools/<tool>/bin/<binary>`. Two tools can share a shim name:

```bash
~/.local/bin/colab -> mighty-colab
~/.local/share/uv/tools/mighty-colab/bin/mighty-colab
~/.local/share/uv/tools/google-colab-cli/bin/colab
```

`which colab` shows the winner; `which -a colab` shows shadowing; `readlink -f` gives the canonical venv binary; `uv tool list` disambiguates.

## The `which` Chain (use before any `tool --help` check)

```bash
which colab
which -a colab               # shows all candidates, order = PATH precedence
ls -l $(which colab)         # symlink? e.g. colab -> mighty-colab
readlink -f $(which colab)   # canonical: ~/.local/share/uv/tools/<tool>/bin/<binary>
uv tool list | grep -E "mighty-colab|google-colab-cli"
colab version
colab --help | grep -q ssh && echo "HAS ssh" || echo "MISSING"
COLAB_BIN=$(readlink -f $(which colab)); echo "COLAB_BIN=$COLAB_BIN"
```

Use `COLAB_BIN` verbatim in `ProxyCommand` and `~/.ssh/config`. Re-derive after every `uv tool install --force`.

## ProxyCommand staleness

`~/.ssh/config` survives reinstalls. Verify:

```bash
cat ~/.ssh/config | grep -A6 "Host colab-agent"
ssh -G colab-agent | grep -i proxycommand   # must match echo $COLAB_BIN
```

Mismatch = stale path → `ModuleNotFoundError: pydantic_core` (if `PYTHONPATH=` prefix missing) or `No such command`.

## Pre-flight pattern (for any workflow before `tool new` / `tool ssh`)

```bash
export PYTHONPATH=""
if ! colab ssh --help >/dev/null 2>&1; then
  echo "ssh missing — reinstalling..."
  uv tool install --force mighty-colab   # fast path
  # or: uv tool install --force git+https://github.com/googlecolab/google-colab-cli.git  # heavy: 52 packages + pyarrow
  which colab; readlink -f $(which colab); colab ssh --help | head
fi
COLAB_BIN=$(readlink -f $(which colab))
```

## Case study

- **Source:** `google-colab-cli` PyPI `0.6.0` lacks `ssh` vs GitHub `main` has it (issue https://github.com/googlecolab/google-colab-cli/issues/102, community answer 5384947488). Live probe 2026-08-24: `mighty-colab 0.2.2` has `ssh`, `google-colab-cli` git-main also has `ssh` via `src/colab_cli/cli.py:26,147` but install is heavy (pyarrow 34 MiB, 2-5 min). `which -a` and `readlink -f` were the only way to tell which install was actually being tested.
- **Stored:** `references/colab-cli-pypi-missing-ssh.md` (full case study).

## Checklist for future `uv tool` installs

- [ ] Run the `which` chain *before* `--help`
- [ ] Re-derive `*_BIN=$(readlink -f $(which <tool>))` after install
- [ ] Check `which -a` for duplicates; `uv tool uninstall <stale>` if needed
- [ ] Verify `ssh -G <alias> | grep proxycommand` matches `echo $*_BIN` when using SSH aliases
