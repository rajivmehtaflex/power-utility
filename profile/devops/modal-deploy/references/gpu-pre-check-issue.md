# GPU Pre-Check: Root Cause and Working Pattern

## History

- **v1.0.0** shipped a `check_gpu.py` that failed with a Modal CLI error.
- **v2.0.1** concluded pre-checks were infeasible and replaced the script with a no-op that always passed — misleading, since `deploy.sh --check` then reported "✅ Check passed" without checking anything.
- **v2.1.0** identified the actual root cause (below) and restored a real, timeout-bounded pre-check.

## The Actual Root Cause

The original script combined `--gpu` with a **function reference**:

```bash
modal shell --gpu T4 my_app.py::some_function -c "nvidia-smi"
```

**Error:** `Cannot specify container configuration arguments (--gpu) when starting a new container from a function reference.`

This is expected behavior: when you pass a function ref, the shell inherits the resource spec from the function's own definition, so per-invocation `--gpu`/`--cpu`/`--memory` flags are rejected.

## The Working Pattern

With **no function reference**, `modal shell` starts a fresh container with whatever resources you request, and `-c` runs a command non-interactively:

```bash
.venv/bin/modal shell --gpu T4 --cpu 1 -c "nvidia-smi -L"
```

If the GPU is allocated, `nvidia-smi -L` prints a line like `GPU 0: Tesla T4 (UUID: ...)` and the command exits 0. This is a genuine allocation test — `templates/check_gpu.py` wraps it with a timeout (default 120s) and prints GPU alternatives on failure.

### Correction to a v2.0.1 claim

v2.0.1 also asserted that `modal run` "doesn't accept `--yes` and requires interactive confirmation." `modal run` executes an ephemeral app without any confirmation prompt; a temp-app pre-check would also work, it is just more code than the `modal shell` one-liner.

## The Honest Trade-off (still true)

A pre-check waits in the **same allocation queue** as your real deployment, so it cannot make a scarce GPU appear faster. What it buys you:

- **Scarce GPUs (H100, H200, B200):** learn within a bounded window (e.g. 120s) that allocation is congested, instead of a full deploy stalling for 10+ minutes.
- **High-availability GPUs (T4, A10):** the pre-check costs roughly as much time as the deploy itself — skip it. `deploy.sh` skips by default; enable with `--check`.

## GPU Alternatives

If a GPU model is unavailable, try these in order:

```python
ALTERNATIVES = {
    "B200": ["H100", "H200", "L40S", "A100", "A10", "L4", "T4"],
    "H200": ["H100", "L40S", "A100", "A10", "L4", "T4"],
    "H100": ["L40S", "A100", "A10", "L4", "T4"],
    "L40S": ["A100", "A10", "L4", "T4"],
    "A100": ["A10", "L4", "T4"],
    "A10":  ["L4", "T4"],
    "L4":   ["T4", "A10"],
    "T4":   ["A10", "L4", "A100"],
}
```

## Related Modal CLI Commands

```bash
# Check authentication
.venv/bin/modal token info

# GPU allocation test (what check_gpu.py runs)
.venv/bin/modal shell --gpu T4 --cpu 1 -c "nvidia-smi -L"

# List deployed apps
.venv/bin/modal app list

# View app logs
.venv/bin/modal app logs <app-name>

# Stop a stuck app
.venv/bin/modal app stop <app-name> --yes

# Deploy
.venv/bin/modal deploy modal_app.py
```
