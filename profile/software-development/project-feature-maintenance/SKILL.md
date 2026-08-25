---
name: project-feature-maintenance
description: Study, plan, harden, and verify project/workspace features with scoped files, derived knowledge, retention policies, and regression tests.
license: MIT
metadata:
  author: Hermes Agent
  hermes_related_skills: plan, test-driven-development, systematic-debugging, requesting-code-review
  hermes_tags: projects, workspaces, file-isolation, knowledge-scoping, data-retention, regression-testing
  platforms: linux, macos, windows
  version: 1.0.0
---

# Project Feature Maintenance

## When to use

Use this skill when a codebase has a Project, workspace, tenant, client, profile, or similar scope that owns files, conversations, derived documents, search indexes, or knowledge. Trigger it when the user asks to:

- Re-study or re-understand a Project/workspace capability after code changes
- Plan or implement file isolation, cleanup, deletion cascades, or scoped search
- Add a project-specific inventory, knowledge, or retrieval path
- Verify that deleting one scope does not affect another
- Review whether behavior is an intentional product policy or an accidental leak

## Core principle

**Separate scope, retention, and derivation before changing code.**

A Project feature often has multiple representations of one uploaded document:

1. Original file stored under a project directory
2. Database registry row
3. Converted Markdown/OCR/index record
4. Search result or agent tool exposure
5. Conversation/thread metadata

Do not assume deleting one representation should delete all representations. First identify the intended retention policy and make the policy explicit in code and tests.

## Investigation workflow

### 1. Map the complete lifecycle

Trace one uploaded file from UI to search:

```text
UI upload
  -> project action callback
  -> original file storage
  -> database registry
  -> conversion/OCR
  -> derived Markdown/index
  -> scoped search or agent tool
```

Also trace deletion:

```text
UI delete
  -> thread cascade
  -> database rows
  -> original project directory
  -> derived Markdown/index
  -> search visibility
```

Inspect the actual call sites, not only the repository helpers. Record the exact scope key used at each boundary.

### 2. Classify each resource

Create a table before implementing changes:

| Resource | Scope | Storage | Delete behavior | Visibility rule |
|---|---|---|---|---|
| Original upload | Project | `project_files/<id>/` | Usually delete with project | Project only |
| Registry row | Project | Database | Delete with project | Project only |
| Converted document | Project or shared | Markdown/index directory | Product decision | Prefix/path filter |
| Threads | Project | Data layer | Delete by tag | Project tag |
| Financial database | Often shared | DuckDB/API | Usually not project-delete-owned | Query/tool policy |

Do not report “isolated” unless every relevant read path is covered. A shared database may remain intentionally shared even when uploaded files are project-scoped.

### 3. Read product documentation for intent

Search `CLAUDE.md`, README files, design notes, and tests for statements such as:

- “shared knowledge pool”
- “intentionally left behind”
- “project files only”
- “General mode”
- “delete cascade”

Treat explicit documentation as a product decision to confirm, not as an accidental bug. If the user wants a behavior change, present it as Scope A/B rather than silently changing the default.

## Safe cleanup design

### Prefer opt-in cleanup first

When current behavior intentionally retains derived knowledge, introduce an explicit API flag before changing the default:

```python
def delete_project(
    project_id,
    *,
    purge_markdown=False,
):
    # Delete project-owned records and original files.
    # Delete derived files only when explicitly requested.
    if purge_markdown:
        purge_project_markdown(project_id)
```

The cleanup helper must:

- Match only the project’s exact scope key
- Return a count or useful result
- Be safe when the directory is missing
- Leave General/shared documents untouched
- Be independently unit-testable

### Use defense-in-depth scope keys

A robust derived-document scope should use:

1. A deterministic filename prefix such as `<project_id>__<stem>.md`
2. A metadata/path header such as `project_files/<project_id>/<name>`
3. A search-time filter enforced by the tool wrapper or closure, not merely by the model’s prompt

The model should not receive a free-form `project_id` argument that it can omit. Bind the active project into the search tool at agent construction time.

### Do not claim impossible legacy repairs

If old flat filenames could have been overwritten, search code cannot recover content that no longer exists. State the limitation plainly and add a regression guard for the current path/header behavior. A migration or recovery project is separate work and must be planned from available source files or backups.

## TDD and verification workflow

Use a vertical RED → GREEN cycle:

1. Add one test for the desired cleanup or isolation behavior.
2. Run only that test and confirm the expected failure.
3. Implement the smallest production change.
4. Re-run the test and confirm it passes.
5. Add the next edge case.
6. Run the focused suite for all changed modules.
7. Run the application/integration tests that exercise the callback path.
8. Run the full suite if practical.

Minimum cleanup tests:

- Project-prefixed derived files are removed by the purge helper
- General-mode files remain
- Another project’s files remain
- Default deletion retains derived files if retention is the current policy
- Explicit purge removes derived files
- Missing derived directory is a no-op

Minimum search tests:

- Project A finds its own file
- Project A cannot find Project B’s same-named file
- Project-scoped search excludes General-mode uploads
- Unscoped General search preserves its intended visibility
- Path/header fallback correctly identifies the owning project

### Separate code failures from fixture failures

When the full suite fails after focused tests pass:

1. Run the failing test alone.
2. Inspect the failure path and fixture/resource path.
3. Compare it with the changed files and baseline result.
4. Do not modify feature code to compensate for missing unrelated databases, PDFs, credentials, or environment fixtures.
5. Report focused results and unrelated full-suite failures separately.

A successful focused verification is meaningful evidence, but do not call the entire suite green when unrelated fixture tests fail.

## Repository and submodule handoff

Before listing commit-ready files or committing implementation changes, determine which Git repository owns each target path:

```bash
git submodule status
git status --short
```

For a parent repository containing submodules:

1. Run `git status --short` and `git diff --name-only` inside each affected submodule.
2. Filter out unrelated artifacts such as `.hermes/` plans, generated PDFs/exports, logs, and attachments.
3. Commit the selected source/test/docs files inside the child submodule first.
4. Return to the parent repository and stage only the changed submodule pointer.
5. Verify child staged files and parent staged submodule state separately:
   ```bash
   git -C path/to/submodule diff --cached --name-only
   git diff --cached --submodule=short
   ```

Clean sibling submodules must not be staged. Explain that a parent commit stores the child commit pointer, not the child source diff. If the user asks only for a filtered file list, do not commit; provide the child file list and the parent pointer step separately.

## Live UI/application verification

When a Project change is meant to be demonstrated in a running app, verify the operational path after code tests pass:

1. Identify the existing service process and listening port before restarting.
2. Stop the old process cleanly; confirm the port is free.
3. Restart from the service directory using the project’s configured environment.
4. Probe the HTTP endpoint and inspect startup logs for readiness/errors.
5. For deletion tests, verify all layers: application event log, project row, project-file rows, original directory, derived Markdown/search visibility, and tagged threads.
6. If the selected retention policy intentionally keeps derived Markdown, report that explicitly rather than treating retention as failed cleanup.

## Productionizing a prototype

When a feature is currently a working prototype but lacks production boundaries, do not jump straight to a rewrite. First record the verified baseline: actual transport, endpoints, persistence model, supported methods, missing security controls, and the current automated-test inventory. Then define acceptance criteria for the production boundary before implementation.

For agent/API integrations, use this sequence:

1. Extract transport-neutral domain/service logic from the prototype.
2. Introduce an application factory with dependency injection so tests can use a deterministic fake agent.
3. Add protocol/model validation and error-envelope tests before wiring the live provider.
4. Replace in-memory task state with an explicit persistence boundary when restart behavior matters.
5. Add authentication, request limits, and SSRF/file validation before enabling remote or multimodal inputs.
6. Implement streaming behind an adapter after confirming the installed provider's actual iterator/API shape.
7. Keep a minimal interoperability fixture separate from the production service if it has intentionally weaker behavior.
8. Run focused unit/security/integration tests before any live-provider smoke test; report missing test files and no-test collection explicitly.

If the user invokes plan mode, inspect only with read-only tools and write only the plan file. Do not create scaffolding, modify configuration, run mutating commands, or claim implementation progress until execution is explicitly authorized.

## Legacy `src/` test harness

When productionizing a Python prototype that has a `src/` layout but no executable tests, establish one vertical tracer slice before building the full suite. Add the smallest import bootstrap or `pyproject.toml` pytest `pythonpath` setting, inject a deterministic fake agent, and use `tmp_path` SQLite databases so collection and tests never depend on provider credentials or runtime storage. Verify RED → GREEN on the tracer, then expand to persistence, API, security, streaming, media, and isolation boundaries. Keep generated databases, coverage output, and caches out of the implementation diff. See `references/legacy-src-test-harness.md` for the reusable setup and assertions.

## Plan and implementation handoff

A good plan should include:

- Exact target files
- Exact no-touch files
- Current behavior and intended behavior
- Scope A: non-breaking opt-in behavior
- Scope B: default-changing behavior
- Tests and expected results
- Known legacy limitations
- Data-retention/privacy implications

Before implementation, re-check the plan against the current code. If a planned test is logically impossible—such as writing two different contents to the same path and expecting both to survive—revise the plan before coding.

## Common pitfalls

- Treating shared derived Markdown as automatically project-owned
- Purging by a broad substring instead of an exact project prefix
- Assuming UI project state automatically reaches the agent; trace the parameter flow
- Giving the model an unbound scope parameter
- Modifying model/provider configuration for a deterministic repository feature
- Changing deletion defaults without a product decision
- Claiming to fix overwritten legacy data
- Running only a full suite and missing the focused regression signal
- Reporting unrelated fixture failures as implementation regressions

## Reference

For the concrete scope/retention/scoped-search pattern and verification recipe, see `references/project-scoped-knowledge.md`.
