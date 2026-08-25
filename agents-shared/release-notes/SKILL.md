---
name: release-notes
description: ">-"
---

# Release Notes: Capabilities & Enhancements Distiller

This skill transforms any user-supplied software release notes, changelogs, or version announcements into clear, actionable reference documents. It filters out routine bug fixes and maintenance patches, isolating only **New Capabilities** and **Enhancements**, and outputs both Markdown tables and styled PDF reports dynamically.

---

## When to Use

Use this skill whenever:
- The user provides release notes, changelogs, or update logs (as pasted text, a file path, or a URL) and asks to summarize, analyze, or filter them.
- The user requests an explanation of new features with simple language, examples, and practical use cases.
- The user asks for a tabular breakdown of release capabilities formatted in Markdown and/or PDF.

---

## Step-by-Step Workflow

### 1. Ingest User-Supplied Release Notes
Accept release notes from the user in any of the following forms:
- **Direct Prompt Text:** Notes pasted directly in the conversation.
- **Local File Path:** A path provided by the user (e.g. `CHANGELOG.md`, `release_notes.txt`). Read the file contents.
- **URL / Repository:** Fetch the release notes from a public web page. For GitHub repositories, use the Exa MCP server (`web_search_exa` to find latest tags and `web_fetch_exa` to read content) to ensure a structured retrieval of the most recent versions.
- *If no release notes are provided in the prompt, ask the user to provide or paste the release notes text or file path before proceeding.*

### 2. Filter Enhancements & New Capabilities
Examine the ingested release notes and strictly separate items:
- **VERSION FILTER (Mandatory):** Exclude any releases containing tags like `nightly`, `preview`, `beta`, `rc`, or `alpha`. Include only stable, production-grade versions.
- **INCLUDE:** New features, new CLI flags, workflow enhancements, API additions, performance boosts, UI improvements, and new configuration options.
- **EXCLUDE:** Routine bug fixes, crash resolutions, permission bypass fixes, internal refactors, and minor security hardening patches (unless they introduce new user-facing configuration or behavior).

### 3. Group into Logical Domains & Build Tabular Structure
Categorize the filtered capabilities into intuitive functional areas (e.g., *Collaboration Features*, *Integrations*, *Developer Workflow*, *UI & Performance*, *Security*).

**Formatting Note:** If the user requests "original values" or "no formatting", remove all Markdown bolding (`**...**`) and code backticks (`` `...` ``) from all columns. Otherwise, use standard highlighting for clarity.

For each capability, formulate:
1. **Capability / Enhancement**: Specific feature name.
2. **Simple Explanation**: Plain English description without unnecessary jargon.
3. **Example**: Clear snippet, CLI command, or interaction pattern.
4. **Real-World Use Case**: Practical scenario explaining when and why a developer would use it.

### 4. Generate Deliverables

#### A. Markdown Deliverable
Create a comprehensive markdown file (e.g. `release_notes_enhancements_<app>_<version>.md` or `release_notes_enhancements.md`) in the user's workspace containing:
- Document Title (`# Title`)
- Subtitle / Brief intro
- Categorized sections with Markdown tables (`## Section Name` followed by 4-column tables)
- Optional summary matrix at the bottom

#### B. Landscape PDF Deliverable
Execute the bundled dynamic PDF generator script using `uv` directly against the generated Markdown file:
```bash
uv run --with reportlab python .agents/skills/release-notes/scripts/generate_release_notes_pdf.py --input <path_to_markdown_file.md> --output <path_to_output_file.pdf>
```

---

## Artifact Governance & User Confirmation

> [!IMPORTANT]
> **MANDATORY CLEANUP STEP**:
> Once deliverables are generated:
> 1. List **all** created files (workspace deliverables, temporary scripts, planning artifacts) in a clear table with clickable markdown links.
> 2. Explicitly ask the user for confirmation before deleting or retaining any files.

---

## Common Pitfalls
- **Hardcoding content:** Never assume fixed version numbers or products; dynamically parse whatever the user provides.
- **Including routine bug fixes:** Ensure fixes (e.g., "Fixed null pointer exception") are excluded unless they change a capability.
- **Vague use cases:** Ensure use cases describe concrete developer workflows rather than generic benefits.
- **Using raw python instead of uv:** Always execute Python scripts with `uv run --with reportlab`.
