#!/usr/bin/env python3
"""Validate an OKF v0.2 bundle for conformance per SPEC.md §11:

1. Every non-reserved .md file has a parseable YAML frontmatter block with a
   non-empty `type` field.
2. Every index.md/log.md present has no frontmatter, except a bundle-root
   index.md, which may carry `okf_version`.
3. Every `resource:` field that is a file:// URI resolves to an existing path.

Usage: python3 validate_okf_bundle.py <bundle_path>
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml

RESERVED = {"index.md", "log.md"}

# Frontmatter delimiters must be "---" alone on their own line (spec §4.1),
# not any substring match — a concept body/description can legitimately
# contain "---" as plain text (e.g. an excerpt from a YAML source file).
DELIM_RE = re.compile(r"(?m)^---[ \t]*$")


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "missing frontmatter delimiter '---'"
    matches = list(DELIM_RE.finditer(text))
    if len(matches) < 2:
        return None, "malformed frontmatter block"
    yaml_text = text[matches[0].end():matches[1].start()]
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as e:
        return None, f"invalid YAML: {e}"
    return data, None


def file_uri_to_path(uri: str) -> Path:
    parsed = urlparse(uri)
    return Path(unquote(parsed.path))


def validate(bundle_root: Path):
    errors = []
    concept_count = 0
    reserved_count = 0

    for path in sorted(bundle_root.rglob("*.md")):
        rel = path.relative_to(bundle_root)
        text = path.read_text(encoding="utf-8", errors="replace")
        is_reserved = path.name in RESERVED

        if is_reserved:
            reserved_count += 1
            is_root_index = path.name == "index.md" and rel.parent == Path(".")
            if text.startswith("---"):
                if not is_root_index:
                    errors.append(f"{rel}: reserved file must not have frontmatter")
                else:
                    data, err = parse_frontmatter(text)
                    if err:
                        errors.append(f"{rel}: {err}")
            continue

        concept_count += 1
        data, err = parse_frontmatter(text)
        if err:
            errors.append(f"{rel}: {err}")
            continue
        if not data.get("type"):
            errors.append(f"{rel}: missing mandatory non-empty 'type' field")

        resource = data.get("resource")
        if resource and resource.startswith("file://"):
            target = file_uri_to_path(resource)
            if not target.exists():
                errors.append(f"{rel}: resource path does not exist: {target}")

    return errors, concept_count, reserved_count


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_okf_bundle.py <bundle_path>")
        sys.exit(1)
    bundle_root = Path(sys.argv[1]).resolve()
    if not bundle_root.is_dir():
        print(f"Not a directory: {bundle_root}")
        sys.exit(1)

    errors, concept_count, reserved_count = validate(bundle_root)

    print(f"Checked {concept_count} concept(s) and {reserved_count} reserved file(s) in {bundle_root}")
    if errors:
        print(f"\n{len(errors)} conformance error(s):")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("✓ Bundle is OKF v0.2 conformant.")


if __name__ == "__main__":
    main()
