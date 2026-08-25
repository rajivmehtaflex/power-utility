# Project-Scoped Knowledge Reference

## Reusable design pattern

For a Project that stores originals and searchable derived documents:

```text
project_files/<project_id>/<original-name>
documents_markdown/<project_id>__<stem>.md
```

The converted document should carry metadata that preserves the project ownership:

```text
--- SOURCE: <original-name> ---
--- PATH: data/project_files/<project_id>/<original-name> ---
```

At agent construction time, bind the active project into the search function:

```python
if project_id is None:
    tool = search_markdown_documents
else:
    def scoped_search(question: str):
        return search_markdown_documents(question, project_id=project_id)
```

This prevents the LLM from accidentally omitting the scope argument.

## Retention decision matrix

| Policy | Original project files | Derived Markdown | Recommended use |
|---|---|---|---|
| Shared pool | Delete | Keep | Cross-engagement reference is valuable |
| Opt-in purge | Delete | Keep by default; remove with flag | Safest compatibility transition |
| Strict deletion | Delete | Delete | Privacy/client offboarding requirement |

Implement the opt-in form first when the current product behavior is shared retention. Only make strict deletion the default after explicit approval and updated tests/docs.

## Purge helper contract

A safe helper should:

- Accept an injectable `docs_dir` for tests
- Resolve the production directory through the project’s existing data-path helper
- Match `f"{project_id}__*.md"` exactly
- Return the number of successfully removed files
- Return zero when the directory does not exist
- Ignore deletion errors per file rather than deleting unrelated files

Test fixture:

```python
(docs_dir / "abc__invoice.md").write_text("project")
(docs_dir / "general_upload.md").write_text("general")
(docs_dir / "other__invoice.md").write_text("other")

assert purge_project_markdown("abc", docs_dir=docs_dir) == 1
assert not (docs_dir / "abc__invoice.md").exists()
assert (docs_dir / "general_upload.md").exists()
assert (docs_dir / "other__invoice.md").exists()
```

## Legacy collision boundary

A historical flat conversion such as `invoice.md` is not recoverable if a second same-named upload overwrote it. A path-header fallback can identify the currently existing document, but cannot restore the lost document. Phrase the result as:

> Current scoped uploads are isolated and regression-tested. Legacy flat files that were already overwritten cannot be recovered without a source copy or backup.

Do not write a test that writes two contents to the same path and pretends both remain available.

## Verification recipe

Run in this order:

```bash
pytest tests/test_projects_repo.py::test_purge_project_markdown_removes_only_project_prefixed_files -q
pytest tests/test_projects_repo.py tests/test_project_data_layer.py tests/test_document_search.py tests/test_app.py -q
pytest tests -q
```

If the focused suite passes but the full suite fails, classify each failure. Missing fixture paths or databases are environment/test-data issues unless the changed code owns those fixtures. Report them separately rather than weakening the Project implementation.
