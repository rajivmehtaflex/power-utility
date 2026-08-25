#!/usr/bin/env python3
"""Verify a root git repo correctly ignores nested subproject repos.

Run from the repo root (or pass --repo PATH). Asserts:
  - No nested-repo prefix is in the index (git ls-files) or committed tree
    (git ls-tree --name-only -r HEAD).
  - The expected top-level loose files ARE tracked.
Exits non-zero on any failure. Prints a clear PASS/FAIL report.

Reusable across any workspace-of-repos init task.
"""
import os
import subprocess
import sys


def run(repo, cmd):
    return subprocess.run(
        f"cd {repo!r} && {cmd}",
        shell=True, capture_output=True, text=True,
    ).stdout


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    repo = os.path.abspath(repo)

    # Nested subproject prefixes that must NEVER be tracked at root.
    nested_prefixes = [
        "adk-exp", "agno-exp", "AudioFast", "az-key-vault-exp", "bertopic_exp",
        "Chrome_Prompt_API", "computer-use-preview", "FC-PLUS-DOCS-UNDERSTANDING",
        "fcp-sites", "freyja_flow_for_get_domain", "g-claude-code-exp",
        "g-data-xero-api", "g-drive-binding", "g-exp", "g-fcp-da-chainlit",
        "g-gemini-cli-exp", "g-hermes-kanban-exp", "g-litellm-exp",
        "g-llama-server", "g-ollama-exp", "g-python-explore", "g-xero-api",
        "gemini_clone", "gemini-flash-exp", "GREO-DEV", "groq_internet_acces",
        "harness-ops", "hermes-android-termux", "incite-dataengineering",
        "lg_deepagent_exp", "local_auth", "make-it-heavy", "maxmini-h3-ops",
        "Mistral-AI-Agents-App", "modal_vm", "modal-webterm", "opencode-exp",
        "pc_work", "pi-agentic-flow-understanding", "pi-local-dev", "POD-POC",
        "pytest-exp", "Python", "remotefolder", "services", "simulator_exp_v1",
        "Skills", "vertex_ai_test", "xero-db-skill", "offline-zerosho-ml",
        "chainlit_frontend",
    ]

    must_exist = {
        ".gitignore", "AGENTS.md", "pi-agent-loop-guide.md", "task_management.md",
        "README_GEMINI.md", "README_QWEN.md", "QWEN.md",
        "azure_keyvault_existing_rg.sh", "azure_keyvault_hello_world_enhanced.sh",
        "gemini-code.sh", "vertex_key.json",
    }

    print(f"=== repo: {repo} ===")
    index = set(run(repo, "git ls-files").splitlines())
    tree = set(run(repo, "git ls-tree --name-only -r HEAD").splitlines())

    ok = True
    for name in nested_prefixes:
        if name in index or any(t.startswith(name + "/") for t in index):
            print(f"FAIL: nested repo {name!r} in index"); ok = False
        if name in tree or any(t.startswith(name + "/") for t in tree):
            print(f"FAIL: nested repo {name!r} in committed tree"); ok = False

    for name in must_exist:
        if name not in tree:
            print(f"FAIL: expected file {name!r} not tracked"); ok = False

    # Nothing staged dirty
    s = run(repo, "git status --short")
    dirty = [ln for ln in s.splitlines() if ln[:1] in "AMD" or ln.startswith(" D")]
    if dirty:
        print("FAIL: staged dirty paths:", dirty); ok = False

    if ok:
        print("ALL CHECKS PASSED")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
