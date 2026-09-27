"""Supplemental package checks for repo-owned/hf-generative-model-converter.

Semantic properties (not exact prose): frontmatter bounds, relative-link
integrity, recipe/schema consistency, catalog/README/VALIDATION_REPORT
consistency, and helper portability from a copied package layout.
"""
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "repo-owned" / "hf-generative-model-converter"

DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500
KNOWN_LICENSES = {"Apache-2.0", "MIT"}
ADVERTISED_TARGETS = {"gguf"}  # targets this package claims as verified


def _frontmatter():
    text = (SKILL / "SKILL.md").read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise AssertionError("SKILL.md has no frontmatter block")
    fields = {}
    for line in m.group(1).splitlines():
        if line.startswith("  ") or not line.strip():
            continue  # metadata block lines handled below
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    # metadata sub-block: collect as flat strings
    in_meta = False
    meta = {}
    for line in m.group(1).splitlines():
        if re.match(r"^metadata:\s*$", line):
            in_meta = True
            continue
        if in_meta:
            km = re.match(r"^  (\w+):\s*(.+)$", line)
            if km:
                meta[km.group(1)] = km.group(2).strip().strip('"')
            else:
                in_meta = False
    return fields, meta, text


class FrontmatterTests(unittest.TestCase):
    def test_name_matches_directory(self):
        fields, _, _ = _frontmatter()
        self.assertEqual(fields["name"], SKILL.name)

    def test_description_bounds_and_trigger(self):
        fields, _, _ = _frontmatter()
        self.assertLessEqual(len(fields["description"]), DESCRIPTION_MAX)
        self.assertTrue(fields["description"].startswith("Use when"),
                        "description must start with 'Use when'")

    def test_compatibility_bounds(self):
        fields, _, _ = _frontmatter()
        self.assertLessEqual(len(fields["compatibility"]), COMPATIBILITY_MAX)

    def test_license_is_known(self):
        fields, _, _ = _frontmatter()
        self.assertIn(fields["license"], KNOWN_LICENSES)

    def test_metadata_values_are_strings(self):
        _, meta, _ = _frontmatter()
        self.assertTrue(meta, "metadata block expected")
        for key, value in meta.items():
            self.assertIsInstance(value, str, f"metadata.{key} must be a string")

    def test_body_line_budget(self):
        _, _, text = _frontmatter()
        body = text.split("---\n", 2)[2]
        self.assertLess(len(body.splitlines()), BODY_MAX_LINES)

    def test_body_advertises_only_verified_targets(self):
        _, _, text = _frontmatter()
        body = text.split("---\n", 2)[2].lower()
        for target in ("onnx", "litert"):
            if target in body:
                qualified = ("planned" in body) or ("no recipe exists" in body) or ("not verified" in body)
                self.assertTrue(
                    qualified,
                    f"{target} must only be mentioned alongside its planned/not-verified status")


class LinkIntegrityTests(unittest.TestCase):
    def test_relative_links_resolve(self):
        broken = []
        for md in SKILL.rglob("*.md"):
            for target in re.findall(r"\]\(([^)#]+?)\)", md.read_text()):
                if target.startswith(("http://", "https://")) or "<" in target:
                    continue  # external links and template placeholders
                if not (md.parent / target).resolve().exists():
                    broken.append(f"{md.relative_to(SKILL)} -> {target}")
        self.assertEqual(broken, [])

    def test_core_files_present(self):
        for rel in (
            "SKILL.md", "references/gguf.md", "references/compatibility.md",
            "references/source-builds.md", "references/validation.md",
            "references/huggingface-upload.md", "assets/recipes.json",
            "assets/manifest.schema.json", "assets/model-card.md",
            "scripts/artifact_manifest.py", "scripts/hub_publish.py",
            "tests/test_artifact_manifest.py", "tests/test_hub_publish.py",
        ):
            self.assertTrue((SKILL / rel).exists(), rel)


class RecipeConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.recipes = json.loads((SKILL / "assets" / "recipes.json").read_text())

    def test_schema_version_and_uniqueness(self):
        self.assertEqual(self.recipes["schema_version"], 1)
        ids = [r["id"] for r in self.recipes["recipes"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_recipe_required_keys(self):
        required = {"id", "revision", "target", "source", "platform", "toolchain",
                    "profile", "commands", "required_files", "validation_policy",
                    "evidence", "limitations"}
        for recipe in self.recipes["recipes"]:
            missing = required - set(recipe)
            self.assertEqual(missing, set(), f"{recipe['id']}: missing {missing}")

    def test_targets_are_known(self):
        for recipe in self.recipes["recipes"]:
            self.assertIn(recipe["target"], {"gguf", "onnx", "litert-lm"})

    @staticmethod
    def _state(value):
        if isinstance(value, dict):
            return value.get("state")
        return value

    def test_verified_targets_have_passed_evidence(self):
        by_target = {}
        for recipe in self.recipes["recipes"]:
            ev = recipe["evidence"]
            build_ok = self._state(ev["source_build"]) == "passed"
            conversion_ok = self._state(ev["conversion"]) == "passed"
            if build_ok and conversion_ok:
                by_target.setdefault(recipe["target"], 0)
                by_target[recipe["target"]] += 1
        for target in ADVERTISED_TARGETS:
            self.assertGreaterEqual(by_target.get(target, 0), 1,
                                    f"{target} advertised as verified but lacks a passed recipe")
        for target in {"onnx", "litert-lm"} - ADVERTISED_TARGETS:
            self.assertNotIn(target, by_target,
                             f"{target} has passed evidence; update ADVERTISED_TARGETS")

    def test_recipe_pins_are_immutable(self):
        for recipe in self.recipes["recipes"]:
            self.assertGreaterEqual(len(recipe["source"]["revision"]), 7)
            self.assertGreaterEqual(len(recipe["toolchain"]["revision"]), 7)


class CatalogConsistencyTests(unittest.TestCase):
    def test_manifest_entry_matches_skill(self):
        manifest = json.loads((REPO / "MANIFEST.json").read_text())
        entries = json.dumps(manifest)
        self.assertIn(SKILL.name, entries)
        self.assertIn("repo-owned", entries)

    def test_readme_indexes_the_skill(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn("hf-generative-model-converter", readme)

    def test_validation_report_records_scope(self):
        report = (REPO / "VALIDATION_REPORT.md").read_text()
        self.assertIn("hf-generative-model-converter", report)


class PortabilityTests(unittest.TestCase):
    def test_copied_package_helpers_run_from_foreign_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            layout = Path(td) / "agent-layout" / "skills" / SKILL.name
            shutil.copytree(SKILL, layout, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
            script = layout / "scripts" / "artifact_manifest.py"
            import os
            for cwd in (Path(td), Path("/")):
                result = subprocess.run(
                    [sys.executable, str(script), "verify",
                     "--stage", str(td), "--manifest", str(td)],
                    capture_output=True, text=True, cwd=cwd,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                # it must run and fail *sanely* (missing inputs), never crash on import paths
                self.assertIn(result.returncode, (1, 2), result.stderr)
                self.assertNotIn("No module named", result.stderr)

    def test_schema_and_recipes_are_valid_json(self):
        for rel in ("assets/recipes.json", "assets/manifest.schema.json"):
            json.loads((SKILL / rel).read_text())


if __name__ == "__main__":
    unittest.main()
