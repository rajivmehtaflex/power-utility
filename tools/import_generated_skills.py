#!/usr/bin/env python3
"""Import generated skill groups while preserving repo-owned content."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


GROUPS = ("agents-shared", "dev-workspace", "profile")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _skill_name(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"missing YAML frontmatter: {skill_file}")
    closing = text.find("\n---", 4)
    if closing < 0:
        raise ValueError(f"unterminated YAML frontmatter: {skill_file}")
    frontmatter = text[4:closing]
    match = re.search(r"^name:\s*([^\s]+)\s*$", frontmatter, re.MULTILINE)
    if not match:
        raise ValueError(f"missing name frontmatter: {skill_file}")
    name = match.group(1)
    if name != skill_file.parent.name or not NAME_RE.fullmatch(name):
        raise ValueError(f"skill name does not match directory: {skill_file}")
    description = re.search(r"^description:\s*(.+)\s*$", frontmatter, re.MULTILINE)
    if not description or not description.group(1).strip():
        raise ValueError(f"missing description frontmatter: {skill_file}")
    return name


def _all_skill_names(root: Path) -> set[str]:
    return {_skill_name(skill_file) for skill_file in root.rglob("SKILL.md")}


def _validate_staged_groups(source: Path, repo: Path) -> dict[str, Path]:
    staged_groups = {group: source / group for group in GROUPS if (source / group).is_dir()}
    staged_names: set[str] = set()
    for staged in staged_groups.values():
        for skill_file in staged.rglob("SKILL.md"):
            name = _skill_name(skill_file)
            if name in staged_names:
                raise ValueError(f"duplicate staged skill name: {name}")
            staged_names.add(name)
    retained_names = _all_skill_names(repo / "repo-owned") if (repo / "repo-owned").exists() else set()
    for group in GROUPS:
        if group not in staged_groups and (repo / group).exists():
            retained_names |= _all_skill_names(repo / group)
    duplicates = staged_names & retained_names
    if duplicates:
        raise ValueError(f"duplicate skill name(s): {', '.join(sorted(duplicates))}")
    return staged_groups


def _description(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    closing = text.find("\n---", 4)
    frontmatter = text[4:closing]
    return re.search(r"^description:\s*(.+)\s*$", frontmatter, re.MULTILINE).group(1).strip()


def rebuild_catalog(repo: Path) -> None:
    manifest_path = repo / "MANIFEST.json"
    if not manifest_path.exists():
        return
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    previous_by_dest = {item.get("dest"): item for item in previous.get("skills", [])}
    skills = []
    for root_name in (*GROUPS, "repo-owned"):
        root = repo / root_name
        if not root.exists():
            continue
        for skill_file in sorted(root.rglob("SKILL.md")):
            name = _skill_name(skill_file)
            dest = skill_file.parent.relative_to(repo).as_posix()
            old = previous_by_dest.get(dest, {})
            relative = skill_file.parent.relative_to(root)
            skills.append({
                "name": name,
                "source": root_name,
                "source_path": old.get("source_path", dest),
                "category": old.get("category", relative.parts[0] if root_name == "profile" and relative.parts else None),
                "dest": dest,
                "description": _description(skill_file),
                "original_fields": old.get("original_fields", {}),
                "spec_compliant": True,
                "warnings": old.get("warnings", []),
            })
    previous["generated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    previous["skills"] = skills
    manifest_path.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
    count = len(skills)
    readme = repo / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = re.sub(r"· \d+ skills", f"· {count} skills", text)
        text = re.sub(r"Install ALL \d+ skills", f"Install ALL {count} skills", text)
        readme.write_text(text, encoding="utf-8")
    report = repo / "VALIDATION_REPORT.md"
    if report.exists():
        text = report.read_text(encoding="utf-8")
        text = re.sub(r"Total: \d+ skills; \d+ spec-compliant; \d+ failed", f"Total: {count} skills; {count} spec-compliant; 0 failed", text)
        report.write_text(text, encoding="utf-8")


def import_generated(source: Path, repo: Path) -> list[str]:
    source = source.resolve()
    repo = repo.resolve()
    if source == repo or source.is_relative_to(repo) or repo.is_relative_to(source):
        raise ValueError("staging directory must not overlap the repository")
    staged_groups = _validate_staged_groups(source, repo)
    if not staged_groups:
        return []
    staging_root = Path(tempfile.mkdtemp(prefix=".generated-import-", dir=repo))
    backups: dict[Path, Path] = {}
    replacements: dict[Path, Path] = {}
    try:
        for group, staged in staged_groups.items():
            replacement = staging_root / group
            shutil.copytree(staged, replacement)
            replacements[repo / group] = replacement
        for target, replacement in replacements.items():
            backup = staging_root / f"backup-{target.name}"
            if target.exists():
                os.replace(target, backup)
                backups[target] = backup
            os.replace(replacement, target)
    except Exception:
        for target in replacements:
            if target.exists() and target not in backups:
                shutil.rmtree(target)
        for target, backup in backups.items():
            if target.exists():
                shutil.rmtree(target)
            if backup.exists():
                os.replace(backup, target)
        raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    rebuild_catalog(repo)
    return list(staged_groups)


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
