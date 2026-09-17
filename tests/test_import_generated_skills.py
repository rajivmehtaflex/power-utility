import tempfile
import unittest
import json
from pathlib import Path

from tools.import_generated_skills import import_generated


class GeneratedImportTests(unittest.TestCase):
    @staticmethod
    def write_skill(path, name):
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test skill\n---\n", encoding="utf-8"
        )

    def test_import_updates_generated_groups_and_preserves_repo_owned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            staged = root / "stage"
            (repo / "repo-owned" / "unsloth-workflows").mkdir(parents=True)
            (repo / "repo-owned" / "unsloth-workflows" / "marker").write_text("keep", encoding="utf-8")
            (repo / "profile" / "old").mkdir(parents=True)
            (repo / "profile" / "old" / "old.txt").write_text("old", encoding="utf-8")
            (staged / "profile" / "new").mkdir(parents=True)
            (staged / "profile" / "new" / "new.txt").write_text("new", encoding="utf-8")
            copied = import_generated(staged, repo)
            self.assertEqual(copied, ["profile"])
            self.assertTrue((repo / "profile" / "new" / "new.txt").exists())
            self.assertFalse((repo / "profile" / "old").exists())
            self.assertEqual((repo / "repo-owned" / "unsloth-workflows" / "marker").read_text(), "keep")

    def test_import_rejects_repository_as_staging_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                import_generated(root, root)

    def test_import_rejects_staged_skill_with_mismatched_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staged = root / "stage"
            repo = root / "repo"
            skill = staged / "profile" / "wrong-dir"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: other-name\ndescription: test\n---\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                import_generated(staged, repo)

    def test_import_rejects_nested_staging_source_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            staged = repo / "profile" / "staging"
            self.write_skill(staged / "profile" / "new", "new")
            self.write_skill(repo / "profile" / "old", "old")
            with self.assertRaises(ValueError):
                import_generated(staged, repo)
            self.assertTrue((staged / "profile" / "new" / "SKILL.md").exists())
            self.assertTrue((repo / "profile" / "old" / "SKILL.md").exists())

    def test_import_validates_all_groups_before_replacing_any_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            staged = root / "staged"
            self.write_skill(repo / "agents-shared" / "old", "old")
            self.write_skill(staged / "agents-shared" / "new", "new")
            self.write_skill(staged / "profile" / "wrong", "different")
            with self.assertRaises(ValueError):
                import_generated(staged, repo)
            self.assertTrue((repo / "agents-shared" / "old" / "SKILL.md").exists())
            self.assertFalse((repo / "agents-shared" / "new").exists())

    def test_import_rejects_duplicate_name_owned_by_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            staged = root / "staged"
            self.write_skill(repo / "repo-owned" / "existing", "existing")
            self.write_skill(staged / "profile" / "existing", "existing")
            with self.assertRaises(ValueError):
                import_generated(staged, repo)

    def test_import_rebuilds_manifest_and_catalog_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            staged = root / "staged"
            repo.mkdir()
            (repo / "MANIFEST.json").write_text(
                json.dumps({"generated": "old", "spec": "https://agentskills.io/specification.md", "skills": []}),
                encoding="utf-8",
            )
            (repo / "README.md").write_text("Spec: x · 0 skills\n# Install ALL 0 skills\n", encoding="utf-8")
            (repo / "VALIDATION_REPORT.md").write_text("Total: 0 skills; 0 spec-compliant; 0 failed\n", encoding="utf-8")
            self.write_skill(staged / "profile" / "new", "new")
            import_generated(staged, repo)
            manifest = json.loads((repo / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual([(item["name"], item["dest"]) for item in manifest["skills"]], [("new", "profile/new")])
            self.assertIn("1 skills", (repo / "README.md").read_text(encoding="utf-8"))
            self.assertIn("Total: 1 skills", (repo / "VALIDATION_REPORT.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
