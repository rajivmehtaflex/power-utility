#!/usr/bin/env python3
"""Import generated skill groups while preserving repo-owned content."""

from __future__ import annotations

import argparse
import shutil
import re
from pathlib import Path


GROUPS = ("agents-shared", "dev-workspace", "profile")


def _validate_group(group: Path) -> None:
    for skill_file in group.rglob("SKILL.md"):
        text = skill_file.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*([^\s]+)\s*$", text, re.MULTILINE)
        if not match:
            raise ValueError(f"missing name frontmatter: {skill_file}")
        if match.group(1) != skill_file.parent.name:
            raise ValueError(f"skill name does not match directory: {skill_file}")


def import_generated(source: Path, repo: Path) -> list[str]:
    source = source.resolve()
    repo = repo.resolve()
    if source == repo:
        raise ValueError("staging directory must be separate from the repository")
    copied: list[str] = []
    for group in GROUPS:
        staged = source / group
        if not staged.exists():
            continue
        _validate_group(staged)
        target = repo / group
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(staged, target)
        copied.append(group)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="separate generated collection directory")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    copied = import_generated(args.source, args.repo)
    print("imported: " + (", ".join(copied) if copied else "no generated groups"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
