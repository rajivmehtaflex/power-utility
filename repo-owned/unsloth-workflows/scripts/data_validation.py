"""Validate the small local dataset formats supported by the built-in workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _content(value: Any) -> str:
    return value if isinstance(value, str) else str(value)


def _chat_error(row: dict[str, Any], line: int) -> str | None:
    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        return f"line {line}: messages must be a non-empty array"
    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if len(roles) != len(messages) or any(role not in {"system", "user", "assistant"} for role in roles):
        return f"line {line}: each message needs role system, user, or assistant"
    if not any(role == "user" for role in roles):
        return f"line {line}: conversation needs a user message"
    assistant = [m for m in messages if m.get("role") == "assistant" and _content(m.get("content", "")).strip()]
    if not assistant:
        return f"line {line}: conversation needs a non-empty assistant response"
    return None


def _alpaca_error(row: dict[str, Any], line: int) -> str | None:
    if not _content(row.get("instruction", "")).strip():
        return f"line {line}: instruction is required"
    if not _content(row.get("output", "")).strip():
        return f"line {line}: output is required"
    return None


def validate_dataset(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    errors: list[str] = []
    hashes: set[str] = set()
    rows = 0
    duplicate_rows = 0
    detected: str | None = None
    try:
        handle = source.open(encoding="utf-8")
    except OSError as exc:
        return {"path": str(source), "rows": 0, "format": None, "errors": [str(exc)], "duplicates": 0}
    with handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
                continue
            if not isinstance(row, dict):
                errors.append(f"line {line_number}: record must be an object")
                continue
            digest = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            if digest in hashes:
                duplicate_rows += 1
            hashes.add(digest)
            if "messages" in row:
                detected = detected or "chatml"
                error = _chat_error(row, line_number)
            elif "instruction" in row or "output" in row:
                detected = detected or "alpaca"
                error = _alpaca_error(row, line_number)
            else:
                error = f"line {line_number}: expected messages or instruction/output fields"
            if error:
                errors.append(error)
    if duplicate_rows:
        errors.append(f"{duplicate_rows} exact duplicate record(s)")
    return {"path": str(source), "rows": rows, "format": detected, "errors": errors, "duplicates": duplicate_rows}
