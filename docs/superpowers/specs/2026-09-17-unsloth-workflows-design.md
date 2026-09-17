# Unsloth Workflows Skill Design

## Goal

Provide a cross-agent skill for understanding and operating Unsloth on Linux/NVIDIA machines. The skill combines framework guidance with a portable shell/Python runner for project-local setup, dataset validation, text SFT, evaluation, and export.

## Boundaries

Discussion is read-only. Preparation creates reviewable configuration/scripts. Execution is limited to the current Linux/NVIDIA shell host and a project-local `.unsloth/venv`. The skill does not manage SSH, cloud GPU provisioning, system drivers, or non-Linux training hosts.

## Architecture

`SKILL.md` routes requests to focused references and the runner. `scripts/unsloth_workflow.py` validates strict JSON configuration and dispatches `doctor`, `setup`, `validate-data`, `train`, `evaluate`, and `export`. Training uses Unsloth Core and TRL through a managed environment; specialized modalities and RL are guided through current upstream examples.

Repo-owned skills live under `repo-owned/` and are preserved when generated skill groups are refreshed. CPU tests use fixtures and subprocess boundaries; a Linux/NVIDIA smoke run is a separate acceptance gate.

## Evidence policy

The skill distinguishes upstream-documented support, locally detected capability, and tested execution. It reports configuration, environment, training, evaluation, and export as separate outcomes and never silently substitutes model, method, precision, template, or split.
