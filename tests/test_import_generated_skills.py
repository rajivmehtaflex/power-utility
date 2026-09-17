import tempfile
import unittest
from pathlib import Path

from tools.import_generated_skills import import_generated


class GeneratedImportTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
