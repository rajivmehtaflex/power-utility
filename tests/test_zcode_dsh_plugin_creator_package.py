"""Supplemental package checks for repo-owned/zcode-dsh-plugin-creator.

Semantic properties (not exact prose): frontmatter bounds and the real
single-line description, required package resources, package-relative link
integrity, monorepo-needle freedom, catalog/README/VALIDATION_REPORT
consistency, and portability of the copied package layout.
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "repo-owned" / "zcode-dsh-plugin-creator"

DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500
KNOWN_LICENSES = {"Apache-2.0", "MIT"}

# The catalog helper (tools/import_generated_skills.py) reads descriptions with
# this single-line regex; the manifest entry must carry the real string it
# extracts, never a folded marker such as ">-".
IMPORTER_DESCRIPTION_RE = r"^description:\s*(.+)\s*$"

AGENTSKILLS_SPEC_URLS = {
    "https://agentskills.io/specification",
    "https://agentskills.io/specification.md",
}

INSTALL_COMMAND = (
    "npx skills add rajivmehtaflex/power-utility --skill zcode-dsh-plugin-creator"
)

# Monorepo-flavored strings a copied package must not depend on.
MONOREPO_NEEDLES = ("power-utility", "repo-owned/", "tools/skill-validation")

REFERENCES = (
    "command.md",
    "tool.md",
    "skill-plugin.md",
    "preset.md",
    "action-card.md",
    "bundle-anatomy.md",
    "verify.md",
)


def _frontmatter():
    text = (SKILL / "SKILL.md").read_text()
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with a '---' frontmatter fence")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("SKILL.md frontmatter has no closing fence")
    frontmatter, body = text[4:end], text[end + len("\n---\n"):]
    fields = {}
    meta = {}
    in_meta = False
    for line in frontmatter.splitlines():
        if re.match(r"^metadata:\s*$", line):
            in_meta = True
            continue
        if in_meta:
            km = re.match(r"^  (\w+):\s*(.+)$", line)
            if km:
                meta[km.group(1)] = km.group(2).strip().strip('"')
                continue
            in_meta = False
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, meta, frontmatter, body


def _manifest_entry():
    manifest = json.loads((REPO / "MANIFEST.json").read_text())
    matches = [s for s in manifest["skills"] if s.get("name") == SKILL.name]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {SKILL.name} manifest entry, got {len(matches)}"
        )
    return manifest, matches[0]


def _link_violations(label, text, base_dir, allowed_http, allow_parent):
    """Check ``](path)`` markdown links: existing, relative, one directory deep."""
    violations = []
    for target in re.findall(r"\]\(([^)#]+?)\)", text):
        if target.startswith(("http://", "https://")):
            if target not in allowed_http:
                violations.append(f"{label}: unexpected external link {target}")
            continue
        if target.startswith("/"):
            violations.append(f"{label}: absolute path {target}")
            continue
        dirs = list(PurePosixPath(target).parts[:-1])
        if allow_parent:
            while dirs and dirs[0] == "..":
                dirs.pop(0)
        if ".." in dirs:
            violations.append(f"{label}: escaping path {target}")
            continue
        if len(dirs) > 1:
            violations.append(f"{label}: deeper than one directory {target}")
            continue
        if not (base_dir / target).resolve().exists():
            violations.append(f"{label}: broken link {target}")
    return violations


class FrontmatterTests(unittest.TestCase):
    def test_frontmatter_block_parses(self):
        fields, _, _, _ = _frontmatter()
        self.assertIn("name", fields)
        self.assertIn("description", fields)

    def test_name_matches_directory(self):
        fields, _, _, _ = _frontmatter()
        self.assertEqual(fields["name"], SKILL.name)
        self.assertEqual(fields["name"], "zcode-dsh-plugin-creator")

    def test_description_bounds_and_single_line(self):
        fields, _, _, _ = _frontmatter()
        description = fields["description"]
        self.assertTrue(description.startswith("Create,"),
                        "description must lead with what the skill does")
        self.assertNotIn("\n", description)
        self.assertNotIn(">-", description,
                         "description must be a real single line, not a folded marker")
        self.assertLessEqual(len(description), DESCRIPTION_MAX)

    def test_description_extraction_matches_importer_regex_and_manifest(self):
        fields, _, frontmatter, _ = _frontmatter()
        m = re.search(IMPORTER_DESCRIPTION_RE, frontmatter, re.MULTILINE)
        self.assertIsNotNone(m, "importer regex must find the description line")
        extracted = m.group(1).strip()
        self.assertEqual(extracted, fields["description"])
        self.assertIn("dsh", extracted)  # the real sentence, not a marker
        _, entry = _manifest_entry()
        self.assertEqual(entry["description"], extracted)

    def test_compatibility_bounds_and_single_line(self):
        fields, _, _, _ = _frontmatter()
        compatibility = fields["compatibility"]
        self.assertNotIn("\n", compatibility)
        self.assertNotIn(">-", compatibility)
        self.assertLessEqual(len(compatibility), COMPATIBILITY_MAX)

    def test_license_is_known(self):
        fields, _, _, _ = _frontmatter()
        self.assertEqual(fields["license"], "MIT")
        self.assertIn(fields["license"], KNOWN_LICENSES)

    def test_metadata_author_and_version_are_strings(self):
        _, meta, _, _ = _frontmatter()
        self.assertEqual(meta.get("author"), "rajivmehtaflex")
        self.assertEqual(meta.get("version"), "0.1.0")
        self.assertIsInstance(meta.get("author"), str)
        self.assertIsInstance(meta.get("version"), str)

    def test_body_line_budget(self):
        _, _, _, body = _frontmatter()
        self.assertLess(len(body.splitlines()), BODY_MAX_LINES)


class PackageResourceTests(unittest.TestCase):
    def test_required_files_present_and_non_empty(self):
        for rel in ("SKILL.md", *(f"references/{name}" for name in REFERENCES)):
            path = SKILL / rel
            self.assertTrue(path.is_file(), rel)
            self.assertGreater(path.stat().st_size, 0, rel)

    def test_references_are_self_consistent(self):
        for name in REFERENCES:
            text = (SKILL / "references" / name).read_text()
            self.assertIn("## ", text, f"{name}: no sections")
            self.assertIn("```", text, f"{name}: no fenced examples")


class LinkIntegrityTests(unittest.TestCase):
    def test_skill_body_links_resolve_within_one_directory(self):
        _, _, _, body = _frontmatter()
        violations = _link_violations(
            "SKILL.md", body, SKILL, AGENTSKILLS_SPEC_URLS, allow_parent=False)
        self.assertEqual(violations, [])

    def test_reference_links_resolve_relative_to_references(self):
        for name in REFERENCES:
            path = SKILL / "references" / name
            violations = _link_violations(
                name, path.read_text(), path.parent,
                AGENTSKILLS_SPEC_URLS, allow_parent=True)
            self.assertEqual(violations, [])


class MonorepoNeedleTests(unittest.TestCase):
    def test_package_files_reference_no_monorepo_only_paths(self):
        for path in SKILL.rglob("*.md"):
            text = path.read_text()
            for needle in MONOREPO_NEEDLES:
                self.assertNotIn(needle, text,
                                 f"{path.relative_to(SKILL)}: monorepo needle {needle!r}")

    def test_external_links_are_allowed_only(self):
        for path in SKILL.rglob("*.md"):
            for url in re.findall(r"https?://[^\s)\"]+", path.read_text()):
                self.assertIn(url, AGENTSKILLS_SPEC_URLS,
                              f"{path.relative_to(SKILL)}: unexpected external link {url}")


class CatalogConsistencyTests(unittest.TestCase):
    def test_exactly_one_entry(self):
        manifest = json.loads((REPO / "MANIFEST.json").read_text())
        names = [s["name"] for s in manifest["skills"] if s["name"] == SKILL.name]
        self.assertEqual(names, [SKILL.name])

    def test_entry_registration_fields(self):
        _, entry = _manifest_entry()
        self.assertEqual(entry["source"], "repo-owned")
        self.assertEqual(entry["source_path"], "repo-owned/zcode-dsh-plugin-creator")
        self.assertEqual(entry["dest"], "repo-owned/zcode-dsh-plugin-creator")
        self.assertEqual(entry["category"], "software-development")
        self.assertIs(entry["spec_compliant"], True)
        self.assertEqual(entry["warnings"], [])

    def test_entry_description_is_frontmatter_description(self):
        fields, _, _, _ = _frontmatter()
        _, entry = _manifest_entry()
        self.assertEqual(entry["description"], fields["description"])
        self.assertNotIn(">-", entry["description"])

    def test_entry_original_fields(self):
        fields, _, _, _ = _frontmatter()
        _, entry = _manifest_entry()
        original = entry["original_fields"]
        self.assertEqual(original["license"], "MIT")
        self.assertEqual(original["compatibility"], fields["compatibility"])
        self.assertEqual(original["metadata_author"], "rajivmehtaflex")
        self.assertEqual(original["metadata_version"], "0.1.0")

    def test_manifest_count_matches_skill_tree(self):
        manifest = json.loads((REPO / "MANIFEST.json").read_text())
        tree_count = len(list(REPO.rglob("SKILL.md")))
        self.assertEqual(len(manifest["skills"]), tree_count)

    def test_root_readme_index_row(self):
        readme = (REPO / "README.md").read_text()
        rows = [line for line in readme.splitlines()
                if "`zcode-dsh-plugin-creator`" in line
                and "| repo-owned | software-development | yes |" in line]
        self.assertEqual(len(rows), 1, "expected exactly one index row")

    def test_root_readme_install_command(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn(INSTALL_COMMAND, readme)

    def test_root_readme_advertised_counts(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn("· 80 skills", readme)
        self.assertIn("Install ALL 80 skills", readme)

    def test_validation_report_addendum(self):
        report = (REPO / "VALIDATION_REPORT.md").read_text()
        self.assertIn("## 2026-11-08 addendum — zcode-dsh-plugin-creator", report)
        self.assertIn("Total: 80 skills; 80 spec-compliant; 0 failed", report)

    def test_validation_report_preserves_historical_totals(self):
        report = (REPO / "VALIDATION_REPORT.md").read_text()
        self.assertIn("Total: 79 skills", report)


class PortabilityTests(unittest.TestCase):
    def test_copied_tree_is_self_contained(self):
        with tempfile.TemporaryDirectory() as td:
            layout = Path(td) / "agent-layout" / "skills" / SKILL.name
            shutil.copytree(SKILL, layout,
                            ignore=shutil.ignore_patterns("__pycache__"))
            # Every relative markdown link inside the copy resolves within it.
            for path in layout.rglob("*.md"):
                for target in re.findall(r"\]\(([^)#]+?)\)", path.read_text()):
                    if target.startswith(("http://", "https://", "/")):
                        continue
                    self.assertTrue(
                        (path.parent / target).resolve().exists(),
                        f"{path.relative_to(layout)}: broken relative link {target}")


if __name__ == "__main__":
    unittest.main()
