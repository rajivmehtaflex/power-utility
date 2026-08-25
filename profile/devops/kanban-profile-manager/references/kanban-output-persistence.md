# Kanban Output Persistence Pitfall

This session surfaced a common Kanban failure mode: a task can complete successfully while the durable artifact is written only inside the worker's **scratch workspace**.

## Observed pattern

- Schema task completed in a scratch workspace, e.g. `/Users/rajivmehtapy/.hermes/kanban/workspaces/t_c2d8bd60/`
- Data-generation task also completed in a scratch workspace, e.g. `/Users/rajivmehtapy/.hermes/kanban/workspaces/t_754fac3a/`
- The workspace was reported as **ephemeral** and deleted at task completion
- No SQLite database was left in the project folder at `.../student-activity-tracking/data/student_activity.db`

## Lesson

A Kanban task that must produce a durable file needs an explicit persistence instruction, such as:

- the final filesystem path for the artifact
- a copy/export step back into the project workspace
- a verification step that checks the file exists at the persistent destination

## Recommended prompt pattern

> Create and initialize the SQLite database for student activity tracking. Write the final database to `/Users/rajivmehtapy/Desktop/SilverOakU/student-activity-tracking/data/student_activity.db`, and verify that the file exists there after generation.

## What the board status means

A task being marked `done` means the **Kanban work item** finished. It does **not** guarantee the generated file survives outside the worker workspace unless the prompt explicitly required persistence.