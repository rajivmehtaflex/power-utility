#!/usr/bin/env python3
"""Deterministic Git-ops synthetic training-data generator.

Runs REAL git commands in throwaway sandboxes, captures genuine outputs
(hashes, reflog entries, conflict markers), and emits TRL-conversational
SFT rows. Ground truth by construction: no teacher model involved.

Validated 2026-08-18 (5 rows, genuine outputs verified by read-back).
Usage: python3 gen_git_synth_data.py [output.jsonl]   (default: alongside script)

Extend by adding a new numbered block: build repo state with run()/write(),
capture outputs, call add_row(category, difficulty, question, answer-with-real-outputs).
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

SYSTEM = (
    "You are a Git specialist. Answer with exact, runnable commands in fenced "
    "code blocks, followed by a brief explanation. If a step is destructive or "
    "irreversible, warn first."
)

rows = []


def run(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args} failed: {r.stderr}")
    return r.stdout.strip()


def write(cwd, rel, content):
    p = pathlib.Path(cwd) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def add_row(category, difficulty, question, answer):
    rows.append({
        "category": category,
        "difficulty": difficulty,
        "source": "deterministic_real_exec",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
    })


# ---------------------------------------------------------------- 1. init+commit
with tempfile.TemporaryDirectory() as d:
    write(d, "README.md", "# Project\n")
    write(d, "src/main.py", "print('hello')\n")
    run(d, "init")
    run(d, "add", "README.md", "src/main.py")
    out_commit = run(d, "commit", "-m", "Initial import")
    real_hash = run(d, "rev-parse", "--short", "HEAD")
    out_log = run(d, "log", "--oneline")

answer = f"""```bash
git init
git add README.md src/main.py
git commit -m "Initial import"
```

**What you should see (from a real run):**

```
$ git commit -m "Initial import"
{out_commit}

$ git log --oneline
{out_log}
```

The `{real_hash}` at the top of the log is your new commit's short hash. `git add <paths>`
stages exactly the named files; use `git add -A` only when you intentionally want
everything, including deletions."""

add_row(
    "init_commit", "basic",
    "I'm in a fresh directory containing README.md and src/main.py. Initialize a git "
    "repository, stage both files, and create the first commit with message "
    '"Initial import". Show the commands and what output confirms success.',
    answer,
)

# ---------------------------------------------------------------- 2. branch + carry changes
with tempfile.TemporaryDirectory() as d:
    run(d, "init", "--initial-branch=main")
    write(d, "app.py", "value = 1\n")
    run(d, "add", ".")
    run(d, "commit", "-m", "base")
    write(d, "app.py", "value = 2  # wip\n")  # uncommitted change
    run(d, "switch", "-c", "feature/login")
    out_status = run(d, "status", "--short")
    out_branch = run(d, "branch", "--show-current")

answer = f"""```bash
git switch -c feature/login
git status --short
git branch --show-current
```

**Real run output:**

```
$ git status --short
{out_status}
$ git branch --show-current
{out_branch}
```

`git switch -c` creates and moves in one step. Uncommitted changes travel with the
working tree — nothing is committed anywhere by a branch switch. ` M app.py`
(space-M) means modified-but-unstaged: exactly the state you left on main.
Only `git stash` or a commit would remove it from the working tree."""

add_row(
    "branching", "basic",
    "I'm on main with an uncommitted change to app.py. Create branch feature/login, "
    "switch to it, and carry the uncommitted change over WITHOUT committing on main. "
    "How do I confirm it worked?",
    answer,
)

# ---------------------------------------------------------------- 3. annotated tag
with tempfile.TemporaryDirectory() as d:
    run(d, "init", "--initial-branch=main")
    write(d, "app.py", "v2\n")
    run(d, "add", ".")
    run(d, "commit", "-m", "release: v2.3.0")
    run(d, "tag", "-a", "v2.3.0", "-m", "Release v2.3.0\n\n- payment reconciliation\n- bug fixes")
    out_show = run(d, "show", "v2.3.0", "--no-patch")

answer = f"""```bash
git tag -a v2.3.0 -m "Release v2.3.0

- payment reconciliation
- bug fixes"
git push origin v2.3.0
git show v2.3.0 --no-patch
```

**Real run — `git show v2.3.0 --no-patch`:**

```
{out_show}
```

An annotated tag is a real git object (type `tag`) storing tagger, date, and message;
a lightweight tag is just a static pointer. Annotated tags can be signed and are what
release tooling expects. Pushing a tag requires naming it explicitly (or `--tags`) —
a plain `git push` does not push tags."""

add_row(
    "tagging_release", "basic",
    "main just got the v2.3 release commit. Create an annotated tag v2.3.0 with a "
    "release-note message, push it to origin, and verify what the tag points to. "
    "Why annotated over lightweight?",
    answer,
)

# ---------------------------------------------------------------- 4. REAL merge conflict
with tempfile.TemporaryDirectory() as d:
    run(d, "init", "--initial-branch=main")
    write(d, "src/config.py", "TIMEOUT = 30\n")
    run(d, "add", ".")
    run(d, "commit", "-m", "add config")
    run(d, "switch", "-c", "feature/auth")
    write(d, "src/config.py", "TIMEOUT = 120\n")
    run(d, "add", ".")
    run(d, "commit", "-m", "raise timeout for auth")
    run(d, "switch", "main")
    write(d, "src/config.py", "TIMEOUT = 45\n")
    run(d, "add", ".")
    run(d, "commit", "-m", "tune timeout on main")
    m = subprocess.run(["git", "merge", "feature/auth"], cwd=d, capture_output=True, text=True)
    assert m.returncode != 0, "expected a conflict"
    conflicted = (pathlib.Path(d) / "src" / "config.py").read_text()
    out_status = run(d, "status", "--short")

answer = f"""The file git writes on conflict (captured from a real reproduction):

```
{conflicted}```

`git status --short` shows:

```
{out_status}
```

Resolve by editing src/config.py to keep only the feature side:

```bash
# edit the file to contain exactly:  TIMEOUT = 120
git add src/config.py
git commit            # concludes the merge with git's default merge message
```

`<<<<<<< HEAD` … `=======` is your current branch (main, TIMEOUT = 45);
`=======` … `>>>>>>> feature/auth` is the incoming branch (120). You may also keep
neither and write a new value — resolution means producing the correct final file,
then `git add` marks it resolved. `git merge --abort` restores the pre-merge state
at any time before you commit."""

add_row(
    "merge_conflict", "intermediate",
    "Merging feature/auth into main reports a conflict in src/config.py (both sides "
    "changed TIMEOUT). Show the exact file contents git produces, then resolve keeping "
    "the feature side (120), and complete the merge.",
    answer,
)

# ---------------------------------------------------------------- 5. REAL reflog recovery
with tempfile.TemporaryDirectory() as d:
    run(d, "init", "--initial-branch=main")
    for i in range(1, 5):
        write(d, f"f{i}.txt", f"content {i}\n")
        run(d, "add", ".")
        run(d, "commit", "-m", f"work #{i}")
    good_tip = run(d, "rev-parse", "--short", "HEAD")
    run(d, "reset", "--hard", "HEAD~3")  # the mistake
    out_log_after = run(d, "log", "--oneline")
    out_reflog = run(d, "reflog")
    run(d, "branch", "recover-work", good_tip)  # the recovery
    out_log_saved = run(d, "log", "--oneline", "recover-work")

answer = f"""The commits are not gone — they became unreachable, and git's reflog still
references them.

```bash
git reflog
git branch recover-work <hash-from-reflog>
git log --oneline recover-work
```

**Real run.** After the bad reset, `git log --oneline` shows only:

```
{out_log_after}
```

but `git reflog` still records every HEAD position:

```
{out_reflog}
```

The `reset: moving to HEAD~3` line is the mistake itself; the entry just above it
is your lost tip (`{good_tip}`). Pointing a new branch at it recovers everything:

```
$ git log --oneline recover-work
{out_log_saved}
```

Recovery is possible because reflog entries keep objects reachable, while `git log`
only walks from branch tips — unreachable-but-existing is invisible to it, not
deleted. It becomes truly impossible once unreachable objects are pruned by garbage
collection (default: 30 days for unreachable, 90 for reachable reflog entries).
Never run `git gc --prune=now` during a recovery."""

add_row(
    "history_safety", "advanced",
    "I just ran `git reset --hard HEAD~3` and realized the discarded commits were "
    "needed. Nothing was pushed. Recover the work, and explain why this is possible "
    "even though `git log` no longer shows those commits.",
    answer,
)

# ---------------------------------------------------------------- write out
out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "git_synth_data.jsonl")
with open(out_path, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"wrote {len(rows)} rows -> {out_path}")
for r in rows:
    print(f"  {r['category']:16s} {r['difficulty']:12s} answer_chars={len(r['messages'][2]['content'])}")
