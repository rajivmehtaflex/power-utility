"""Supplemental package checks for repo-owned/explainify.

Semantic properties (not exact prose): frontmatter bounds and the real
single-line description, required package resources, package-relative link
integrity, catalog/README/VALIDATION_REPORT consistency, and preflight
portability from a copied package layout with no monorepo context.
"""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from tools.import_generated_skills import import_generated, rebuild_catalog

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "repo-owned" / "explainify"

DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500
KNOWN_LICENSES = {"Apache-2.0", "MIT"}

# The catalog helper (tools/import_generated_skills.py) reads descriptions with
# this single-line regex; the manifest entry must carry the real string it
# extracts, never a folded marker such as ">-".
IMPORTER_DESCRIPTION_RE = r"^description:\s*(.+)\s*$"

# External links allowed in packaged markdown: the Agent Skills specification
# anywhere, plus (in references/ only, per the plan's attribution policy) the
# official ASD-STE100 standard the writing profile is inspired by.
AGENTSKILLS_SPEC_URLS = {
    "https://agentskills.io/specification",
    "https://agentskills.io/specification.md",
}
OFFICIAL_STANDARD_URLS = AGENTSKILLS_SPEC_URLS | {
    "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf",
}

INSTALL_COMMAND = "npx skills add rajivmehtaflex/power-utility --skill explainify"
EVIDENCE_POINTER = "`docs/superpowers/verification/explainify/results.md`"

# Monorepo-flavored strings a copied package must not depend on. The single
# tolerated forms: the README's public install-command repo id and its one
# evidence pointer, and provenance comments naming a packaged file via its
# repo-owned/explainify/... prefix (the referenced file ships in the copy).
MONOREPO_NEEDLES = ("repo-owned/", "power-utility", "tools/skill-validation")
PACKAGE_PREFIX = "repo-owned/explainify/"


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
        raise AssertionError(f"expected exactly one {SKILL.name} manifest entry, got {len(matches)}")
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
        self.assertEqual(fields["name"], "explainify")

    def test_description_bounds_and_single_line_trigger(self):
        fields, _, _, _ = _frontmatter()
        description = fields["description"]
        self.assertTrue(description.startswith("Use when"),
                        "description must start with 'Use when'")
        self.assertNotIn("\n", description)
        self.assertNotIn(">-", description,
                         "description must be a real single line, not a folded marker")
        self.assertLessEqual(len(description), DESCRIPTION_MAX)

    def test_description_extraction_matches_importer_regex_and_manifest(self):
        # The catalog helper extracts descriptions with one single-line regex;
        # that extraction must yield the full description, and the manifest
        # entry must store exactly that real string rather than ">-".
        fields, _, frontmatter, _ = _frontmatter()
        m = re.search(IMPORTER_DESCRIPTION_RE, frontmatter, re.MULTILINE)
        self.assertIsNotNone(m, "importer regex must find the description line")
        extracted = m.group(1).strip()
        self.assertEqual(extracted, fields["description"])
        self.assertIn("explainify", extracted)  # the real sentence, not a marker
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
        self.assertEqual(meta.get("author"), "rajivmehtapy")
        self.assertEqual(meta.get("version"), "0.2.1")
        self.assertIsInstance(meta.get("author"), str)
        self.assertIsInstance(meta.get("version"), str)

    def test_body_line_budget(self):
        _, _, _, body = _frontmatter()
        self.assertLess(len(body.splitlines()), BODY_MAX_LINES)


class PackageResourceTests(unittest.TestCase):
    def test_required_files_present_and_non_empty(self):
        for rel in (
            "SKILL.md", "README.md", "LICENSE",
            "scripts/check_env.py", "scripts/render_video.py",
            "references/asd-ste100.md", "references/video-style.md",
            "assets/storyboard.schema.json", "tests/test_video_contract.py",
        ):
            path = SKILL / rel
            self.assertTrue(path.is_file(), rel)
            self.assertGreater(path.stat().st_size, 0, rel)

    def test_license_text(self):
        license_text = (SKILL / "LICENSE").read_text()
        self.assertTrue(license_text.startswith("MIT License"))
        self.assertIn("Copyright (c) 2026 rajivmehtapy", license_text)

    def test_storyboard_schema_contract(self):
        schema = json.loads((SKILL / "assets" / "storyboard.schema.json").read_text())
        self.assertIn("2020-12", schema["$schema"])
        self.assertEqual(sorted(schema["properties"]["schema_version"]["enum"]), ["1.0", "1.1"])


class LinkIntegrityTests(unittest.TestCase):
    def test_skill_body_links_resolve_within_one_directory(self):
        _, _, _, body = _frontmatter()
        violations = _link_violations(
            "SKILL.md", body, SKILL, AGENTSKILLS_SPEC_URLS, allow_parent=False)
        self.assertEqual(violations, [])

    def test_reference_links_resolve_relative_to_references(self):
        for rel in ("asd-ste100.md", "video-style.md"):
            path = SKILL / "references" / rel
            violations = _link_violations(
                rel, path.read_text(), path.parent, OFFICIAL_STANDARD_URLS,
                allow_parent=True)  # ../assets/ and ../scripts/ stay inside the package
            self.assertEqual(violations, [])


class CatalogConsistencyTests(unittest.TestCase):
    def test_exactly_one_explainify_entry(self):
        manifest = json.loads((REPO / "MANIFEST.json").read_text())
        names = [s["name"] for s in manifest["skills"] if s["name"] == SKILL.name]
        self.assertEqual(names, [SKILL.name])

    def test_entry_registration_fields(self):
        _, entry = _manifest_entry()
        self.assertEqual(entry["source"], "repo-owned")
        self.assertEqual(entry["source_path"], "repo-owned/explainify")
        self.assertEqual(entry["dest"], "repo-owned/explainify")
        self.assertEqual(entry["category"], "creative")
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
        self.assertEqual(original["metadata_author"], "rajivmehtapy")
        self.assertEqual(original["metadata_version"], "0.2.1")

    def test_manifest_count_matches_skill_tree(self):
        manifest = json.loads((REPO / "MANIFEST.json").read_text())
        tree_count = len(list(REPO.rglob("SKILL.md")))
        self.assertEqual(len(manifest["skills"]), tree_count)
        self.assertEqual(tree_count, 75)

    def test_root_readme_index_row(self):
        readme = (REPO / "README.md").read_text()
        rows = [line for line in readme.splitlines()
                if "`explainify`" in line and "| repo-owned | creative | yes |" in line]
        self.assertEqual(len(rows), 1, "expected exactly one explainify index row")

    def test_root_readme_install_command(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn(INSTALL_COMMAND, readme)

    def test_root_readme_advertised_counts(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn("· 75 skills", readme)
        self.assertIn("Install ALL 75 skills", readme)

    def test_validation_report_addendum(self):
        report = (REPO / "VALIDATION_REPORT.md").read_text()
        self.assertIn("## 2026-10-02 addendum — explainify", report)
        self.assertIn("Total: 75 skills; 75 spec-compliant; 0 failed", report)

    def test_validation_report_preserves_historical_totals(self):
        report = (REPO / "VALIDATION_REPORT.md").read_text()
        self.assertIn("Total: 73 skills", report)
        self.assertIn("Total: 74 skills", report)


class PortabilityTests(unittest.TestCase):
    def _copied_layout(self, td):
        layout = Path(td) / "agent-layout" / "skills" / SKILL.name
        shutil.copytree(SKILL, layout, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
        return layout

    def _run_preflight(self, layout, cwd, *args):
        return subprocess.run(
            [sys.executable, str(layout / "scripts" / "check_env.py"), *args],
            capture_output=True, text=True, cwd=cwd, timeout=120,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_writing_preflight_runs_from_foreign_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            layout = self._copied_layout(td)
            result = self._run_preflight(layout, Path(td), "--format", "asd-ste100")
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_video_preflight_json_contract_from_foreign_cwd(self):
        # The preflight must report the environment accurately from any cwd:
        # exit 0 + pass=true on hosts with the video toolchain, exit 1 +
        # pass=false with actionable hints where it is absent (e.g. bare CI
        # runners of sibling workflows, which run this suite without ffmpeg).
        # Asserting the contract — not the host's toolchain — keeps the test
        # meaningful in both environments.
        with tempfile.TemporaryDirectory() as td:
            layout = self._copied_layout(td)
            result = self._run_preflight(
                layout, Path(td), "--format", "explainer-video", "--json")
            self.assertIn(result.returncode, (0, 1),
                          result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            marker = result.stdout.rfind("\n{")
            self.assertGreater(marker, -1, "no JSON object in preflight output")
            payload = json.loads(result.stdout[marker + 1:])
            self.assertEqual(payload["format"], "explainer-video")
            self.assertIsInstance(payload["pass"], bool)
            self.assertEqual(payload["pass"], result.returncode == 0)
            self.assertTrue(payload["checks"])
            self.assertEqual(all(check["ok"] for check in payload["checks"]),
                             payload["pass"])
            if payload["pass"]:
                self.assertIn("preflight: PASS", result.stdout)
            else:
                self.assertIn("preflight: FAIL", result.stdout)
                self.assertIn("install with", result.stdout)

    def test_copied_tree_references_no_monorepo_only_paths(self):
        with tempfile.TemporaryDirectory() as td:
            layout = self._copied_layout(td)
            offenders = []
            for path in sorted(layout.rglob("*")):
                if not path.is_file() or path.suffix not in {"", ".md", ".py", ".json", ".txt"}:
                    continue
                rel = path.relative_to(layout)
                text = path.read_text(errors="replace")
                if rel == Path("README.md"):
                    # The README may carry the public install command's repo id
                    # (one "power-utility" per command) and its single evidence
                    # pointer; no other monorepo flavor is allowed there.
                    self.assertEqual(text.count("power-utility"),
                                     text.count(INSTALL_COMMAND))
                    self.assertNotIn("repo-owned/", text)
                    self.assertNotIn("tools/skill-validation", text)
                    self.assertIn(EVIDENCE_POINTER, text)
                    continue
                for needle in MONOREPO_NEEDLES:
                    start = 0
                    while True:
                        idx = text.find(needle, start)
                        if idx == -1:
                            break
                        start = idx + 1
                        # Tolerated only as a provenance pointer to a file that
                        # actually ships inside this copied package
                        # (scripts/render_video.py names its packaged
                        # references/video-style.md this way).
                        context = text[idx:]
                        if context.startswith(PACKAGE_PREFIX):
                            rest = context[len(PACKAGE_PREFIX):].split()[0].strip("`\"'.,;)")
                            if rest and (layout / rest).is_file():
                                continue
                        offenders.append(f"{rel}: {needle}")
            self.assertEqual(offenders, [])


# Plan M3, second checkbox: refresh preservation and generated-collision
# rejection. Every exercise below runs against disposable repository copies
# under tempfile.TemporaryDirectory(); the working checkout and live sources
# are never import targets.


def _write_skill(path, name):
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: generated probe skill\n---\n",
        encoding="utf-8",
    )


def _seed_disposable_repo(root):
    """Scaffold a throwaway repo holding the real owned package and entry."""
    repo = root / "repo"
    shutil.copytree(SKILL, repo / "repo-owned" / SKILL.name,
                    ignore=shutil.ignore_patterns("__pycache__", ".venv"))
    _, entry = _manifest_entry()  # embed the real catalog entry verbatim
    (repo / "MANIFEST.json").write_text(json.dumps({
        "generated": "2026-10-02T00:00:00+00:00",
        "spec": "https://agentskills.io/specification.md",
        "skills": [copy.deepcopy(entry)],
    }, indent=2) + "\n", encoding="utf-8")
    return repo


def _tree_digest(directory):
    """Map every file under ``directory`` to a hash of its exact bytes."""
    return {
        path.relative_to(directory).as_posix():
            hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _explainify_entry(repo):
    manifest = json.loads((repo / "MANIFEST.json").read_text(encoding="utf-8"))
    matches = [s for s in manifest["skills"] if s.get("name") == SKILL.name]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {SKILL.name} entry, got {len(matches)}")
    return manifest, matches[0]


class RefreshPreservationTests(unittest.TestCase):
    """A normal generated refresh leaves the owned skill fully intact."""

    def _refreshed_repo(self, root):
        """Seed a disposable repo, snapshot state, then import a staged group."""
        repo = _seed_disposable_repo(root)
        owned = repo / "repo-owned" / SKILL.name
        before = {"digest": _tree_digest(owned),
                  "entry": copy.deepcopy(_explainify_entry(repo)[1])}
        _write_skill(repo / "profile" / "stale-generated", "stale-generated")
        staging = root / "staging"
        _write_skill(staging / "profile" / "refresh-probe", "refresh-probe")
        copied = import_generated(staging, repo)
        return repo, owned, before, copied

    def test_normal_refresh_replaces_only_the_generated_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _, _, copied = self._refreshed_repo(Path(tmp))
            self.assertEqual(copied, ["profile"])
            self.assertTrue((repo / "profile" / "refresh-probe" / "SKILL.md").is_file())
            self.assertFalse((repo / "profile" / "stale-generated").exists(),
                             "stale generated content must be replaced wholesale")

    def test_normal_refresh_leaves_owned_package_bytes_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, owned, before, _ = self._refreshed_repo(Path(tmp))
            self.assertEqual(_tree_digest(owned), before["digest"])

    def test_normal_refresh_preserves_the_explainify_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _, before, _ = self._refreshed_repo(Path(tmp))
            manifest, entry = _explainify_entry(repo)
            self.assertEqual({s["name"] for s in manifest["skills"]},
                             {"explainify", "refresh-probe"})
            for field in ("name", "source", "source_path", "category",
                          "dest", "description"):
                self.assertEqual(entry[field], before["entry"][field], field)
            self.assertEqual(entry["original_fields"],
                             before["entry"]["original_fields"])
            self.assertEqual(entry["warnings"], before["entry"]["warnings"])
            self.assertIs(entry["spec_compliant"], True)
            # The hand-seeded catalog state itself survives, not just equality
            # with whatever the previous manifest happened to contain.
            self.assertEqual(entry["category"], "creative")
            self.assertEqual(entry["original_fields"]["license"], "MIT")
            self.assertEqual(entry["original_fields"]["metadata_author"],
                             "rajivmehtapy")
            self.assertEqual(entry["original_fields"]["metadata_version"], "0.2.1")

    def test_rebuild_catalog_preserves_seeded_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _seed_disposable_repo(Path(tmp))
            _, seeded = _manifest_entry()  # the real entry the seed embedded
            rebuild_catalog(repo)
            _, entry = _explainify_entry(repo)
            self.assertEqual(entry["source"], "repo-owned")
            self.assertEqual(entry["source_path"], "repo-owned/explainify")
            self.assertEqual(entry["dest"], "repo-owned/explainify")
            self.assertEqual(entry["category"], seeded["category"])
            self.assertEqual(entry["category"], "creative")
            self.assertEqual(entry["original_fields"], seeded["original_fields"])
            self.assertEqual(entry["warnings"], seeded["warnings"])
            self.assertEqual(entry["warnings"], [])
            self.assertIs(entry["spec_compliant"], True)


class CollisionRejectionTests(unittest.TestCase):
    """A staged generated duplicate of the owned name aborts before replacing."""

    def _collision_repo(self, root):
        repo = _seed_disposable_repo(root)
        _write_skill(repo / "profile" / "existing-generated", "existing-generated")
        staging = root / "staging"
        _write_skill(staging / "profile" / SKILL.name, SKILL.name)
        return repo, staging

    def test_staged_duplicate_of_owned_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, staging = self._collision_repo(Path(tmp))
            with self.assertRaises(ValueError) as ctx:
                import_generated(staging, repo)
            message = str(ctx.exception)
            self.assertIn("duplicate skill name", message)
            self.assertIn("explainify", message)

    def test_rejected_collision_replaces_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, staging = self._collision_repo(Path(tmp))
            owned_digest = _tree_digest(repo / "repo-owned" / SKILL.name)
            profile_digest = _tree_digest(repo / "profile")
            manifest_bytes = (repo / "MANIFEST.json").read_bytes()
            with self.assertRaises(ValueError):
                import_generated(staging, repo)
            self.assertEqual(_tree_digest(repo / "profile"), profile_digest,
                             "pre-existing generated group must remain untouched")
            self.assertEqual(_tree_digest(repo / "repo-owned" / SKILL.name),
                             owned_digest)
            self.assertEqual((repo / "MANIFEST.json").read_bytes(), manifest_bytes,
                             "manifest must not be rewritten when validation aborts")

if __name__ == "__main__":
    unittest.main()
