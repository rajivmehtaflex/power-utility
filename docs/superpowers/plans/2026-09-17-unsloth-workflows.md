# Unsloth Workflows Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portable Agent Skills-compliant Unsloth workflow skill for Linux/NVIDIA projects.

**Architecture:** Keep a short routing skill with focused references and a dependency-light Python CLI. The CLI owns project-local setup and common text SFT/evaluation/export entrypoints; advanced workflows remain documented and task-adapted from official examples.

**Tech Stack:** Agent Skills Markdown, Python 3.12 standard library, `uv`, Unsloth Core, Transformers, Datasets, PEFT, TRL, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-unsloth-workflows-design.md`

## Global Constraints

- Execution platform is Linux with NVIDIA GPU access.
- Project environment is `.unsloth/venv`; system drivers and unrelated environments are never modified.
- Discuss and `--dry-run` modes are read-only.
- Repo-owned skill content is preserved during generated collection refresh.
- Linux/NVIDIA end-to-end smoke evidence is required before claiming full release readiness.

---

### Task 1: Skill package and strict runner

**Files:**
- Create: `repo-owned/unsloth-workflows/SKILL.md`
- Create: `repo-owned/unsloth-workflows/references/*.md`
- Create: `repo-owned/unsloth-workflows/scripts/*.py`
- Test: `repo-owned/unsloth-workflows/tests/test_workflow.py`

- [x] Define Discuss, Prepare, and Execute modes and route framework references.
- [x] Add strict JSON loading and validation for model, data, training, evaluation, and export sections.
- [x] Add read-only `doctor`, `--dry-run`, and dataset validation commands.
- [x] Add project-local environment planning and execution helpers.
- [x] Add reusable SFT, evaluation, and export scripts with recorded metadata.
- [x] Add CPU tests for valid/invalid data, duplicates, dry-run mutation safety, platform reporting, and unknown keys.

### Task 2: Repository integration

**Files:**
- Create: `tools/import_generated_skills.py`
- Create: `.github/workflows/unsloth-workflows.yml`
- Modify: `README.md`, `VALIDATION_REPORT.md`, `MANIFEST.json`

- [x] Document repo-owned installation and separate staging import behavior.
- [x] Add a helper that rejects the repository as staging source and updates only generated groups.
- [x] Add CPU CI for tests and syntax compilation.
- [x] Add the `repo-owned/unsloth-workflows` entry to `MANIFEST.json` with current metadata.

### Task 3: Linux/NVIDIA validation

**Files:**
- Create: a temporary Linux/NVIDIA smoke project outside Git
- Record: sanitized command, versions, metrics, and artifact evidence

- [ ] Run setup twice and verify environment reuse.
- [ ] Run 10-step LoRA and QLoRA jobs using a small public model and synthetic data.
- [ ] Resume a checkpoint, evaluate held-out data, reload exports, and verify GGUF inference.
- [ ] Update validation report with evidence and tested combinations.

## Acceptance

CPU tests, syntax checks, Agent Skills validation, and repository preservation checks must pass. Full release status additionally requires the Linux/NVIDIA smoke run; until then the repository must state that GPU evidence is pending.
