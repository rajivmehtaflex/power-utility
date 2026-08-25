# Live-Process-Safe Hermes Cleanup

Use this reference when cleanup is requested while Hermes Desktop, the gateway, or a profile may still be running.

## 1. Detect active Hermes processes

```bash
pgrep -alf 'hermes|electron|gateway'
```

Do not interpret the command's own inventory shell as a Hermes process. Focus on the long-lived gateway, Desktop/Electron, profile servers, MCP watchdogs, and active workers.

## 2. Detect open files before deletion

```bash
lsof -nP | python3 -c 'import sys; root="/.hermes"; [print(line, end="") for line in sys.stdin if ".hermes" in line]'
```

Prefer filtering in Python rather than relying on shell text filters when paths may contain spaces. Build an exact set of open paths and skip any candidate that is open. For a directory candidate, skip it if any open path is below that directory.

Typical active paths include:

- `logs/agent.log`, `gateway.log`, `errors.log`, `gui.log`, and `mcp-stderr.log`
- `state.db`, `state.db-wal`, `state.db-shm`
- `memory_store.db` and its SQLite sidecars
- Runtime binaries and imported extension modules

## 3. Safe operating modes

### Preferred mode: clean shutdown

1. Quit Hermes Desktop and stop gateway/profile processes through normal controls.
2. Re-run `pgrep` and `lsof`.
3. Delete approved candidates only after targeted files are no longer open.

### Fallback mode: live-session cleanup

If stopping Hermes would interrupt the current user session:

1. Delete only candidates confirmed not open.
2. Skip active logs and database sidecars.
3. Do not remove runtime directories, dependencies, source-checkout `release/` outputs in use, or active virtual environments.
4. Explain that Hermes may recreate caches, `.update_check`, logs, and `__pycache__` immediately.
5. Re-measure after the final smoke test, not only immediately after deletion.

## 4. Exact path guards

Resolve every candidate and refuse anything outside `$HERMES_HOME`. Protect these exact roots by default:

- `$HERMES_HOME/config.yaml`
- `$HERMES_HOME/.env`
- `$HERMES_HOME/auth.json`
- `$HERMES_HOME/state.db*`
- `$HERMES_HOME/memory_store.db*`
- `$HERMES_HOME/sessions/`
- `$HERMES_HOME/profiles/`
- `$HERMES_HOME/memories/`
- `$HERMES_HOME/skills/`
- `$HERMES_HOME/shared/`
- `$HERMES_HOME/kanban.db`

Do not implement protection by rejecting any path containing a basename such as `skills` or `profiles`; source dependencies can contain directories with those names. Protect the intended absolute roots, then classify profile logs or nested caches separately if explicitly approved.

## 5. Accounting and verification

Record these values separately:

- Candidate bytes before deletion
- Bytes deleted by category
- Open candidates skipped
- Bytes recreated after Hermes resumes or the smoke test runs
- Final `$HERMES_HOME` size
- Optional Git maintenance reclaim

After cleanup, run:

```bash
hermes doctor
hermes chat -q 'Reply with exactly: cleanup-smoke-test'
```

Then verify databases read-only:

```bash
python3 - <<'PY'
import sqlite3
from pathlib import Path
for name in ('state.db', 'memory_store.db'):
    path = Path.home() / '.hermes' / name
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    print(name, con.execute('PRAGMA integrity_check').fetchone()[0])
    con.close()
PY
```

Report “deletion-phase reclaim” separately from “final net change.” A successful cleanup can still show caches or logs again because the running agent regenerated them.
