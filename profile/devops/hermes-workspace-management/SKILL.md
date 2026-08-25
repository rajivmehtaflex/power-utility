---
name: hermes-workspace-management
description: Manage and clean up Hermes Desktop Project workspaces.
license: MIT
metadata:
  author: Hermes Agent
  hermes_tags: hermes, projects, workspace, maintenance, cleanup
  platforms: linux, macos, windows
  version: 1.0.0
---

# Hermes Workspace Management

This skill provides the workflow for auditing and cleaning up the "Projects" sidebar in the Hermes Desktop app to prevent clutter and ensure only active work is visible.

## Workflow: Project Cleanup

When a user wants to "hide" or remove old projects based on a time threshold (e.g., "only keep projects from the last 20 days"):

1. **List Projects**: Use the `project_list` tool (or `hermes project list` in terminal) to get the current set of configured workspaces and their primary paths.
2. **Audit Staleness**:
   - Run `stat` on the primary paths to find the last modification date.
   - On macOS: `stat -f "%N: %Sm" <paths>`
   - On Linux: `stat -c "%n: %y" <paths>`
3. **Identify Targets**: Compare the modification dates against the user's requested threshold.
4. **Archive/Hide**: Use the `archive` command to remove the project from the active sidebar view.
   - Command: `hermes project archive <project-name-or-slug>`

## Pitfalls & Lessons

- **Invalid Command**: The command `hermes project remove` does **not** exist. To hide a project from the sidebar without deleting its metadata or underlying files, use `hermes project archive`.
- **Ghost Projects**: Projects may appear in the `project_list` but have no corresponding directory on disk (e.g., if the folder was deleted manually). These should always be archived/cleaned up.
- **Active Project**: Be careful not to archive the currently active project; ensure the user is switched to a valid project before performing bulk archiving.

## Verification
- Run `hermes project list` after archiving to verify the project is no longer in the active list.
- Refresh the Hermes Desktop app sidebar to confirm the visual change.
