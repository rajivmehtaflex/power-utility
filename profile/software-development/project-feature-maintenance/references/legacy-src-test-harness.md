# Legacy `src/` Repository Test Harness

Use this reference when productionizing a Python prototype in a repository that has a `src/` layout but no executable tests yet.

## Sequence

1. Confirm the manifest, existing import paths, and current test inventory.
2. Write one vertical tracer test for the boundary being added.
3. If pytest cannot import `src` packages, add the smallest test-only bootstrap first, then move the setting into `pyproject.toml`:

```python
# tests/conftest.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
```

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

4. Inject a deterministic fake agent with `run()` and `stream()` methods. Unit/API tests must not require a live provider key.
5. Give every SQLite repository test `tmp_path / "tasks.db"`; never use the application runtime database.
6. Run the single test RED, implement the smallest slice, run it GREEN, and then run the full suite before refactoring.

## Boundary assertions

- `TestClient` proves the FastAPI boundary while the fake agent proves session/file forwarding.
- Reopening the same temporary SQLite database proves persistence across process-like lifecycles.
- Separate external identifiers prove context/session isolation.
- Streaming tests assert event ordering, not wall-clock timing.
- Media tests reject local paths, loopback/private URLs, unsupported MIME types, and unallow-listed remote hosts before provider invocation.

## Hygiene

Generated SQLite databases, coverage files, and caches must be ignored or removed after verification. Keep runtime artifacts out of the feature diff.
