import json
import os
import subprocess
import sys
import tempfile
import unittest
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = SKILL_ROOT / "scripts" / "unsloth_workflow.py"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from data_validation import messages_from_record, validate_dataset_pair  # noqa: E402


class WorkflowCliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(ENTRYPOINT), *args],
            cwd=cwd or SKILL_ROOT,
            text=True,
            capture_output=True,
        )

    def test_validate_data_accepts_chat_jsonl_and_reports_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "train.jsonl"
            dataset.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "hello"},
                            {"role": "assistant", "content": "hi"},
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.run_cli("validate-data", "--dataset", str(dataset))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["rows"], 1)
            self.assertEqual(payload["format"], "chatml")
            self.assertEqual(payload["errors"], [])

    def test_validate_data_rejects_missing_assistant_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "bad.jsonl"
            dataset.write_text(
                json.dumps({"messages": [{"role": "user", "content": "hello"}]})
                + "\n",
                encoding="utf-8",
            )
            result = self.run_cli("validate-data", "--dataset", str(dataset))
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["errors"])

    def test_train_dry_run_does_not_create_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            config = project / "run.json"
            output = project / "outputs"
            config.write_text(
                json.dumps(
                    {
                        "model": {"name": "Qwen/Qwen2.5-0.5B-Instruct"},
                        "data": {"train": "train.jsonl", "eval": "eval.jsonl"},
                        "training": {"method": "qlora", "output_dir": str(output)},
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "train", "--project", str(project), "--config", str(config), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(output.exists())
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "train")
            self.assertTrue(payload["dry_run"])

    def test_doctor_is_read_only_and_reports_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            result = self.run_cli("doctor", "--project", str(project))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("platform", payload)
            self.assertFalse((project / ".unsloth").exists())

    def test_setup_dry_run_is_read_only_even_when_host_is_not_linux(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            result = self.run_cli("setup", "--project", str(project), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertFalse((project / ".unsloth").exists())

    def test_config_rejects_unknown_keys_before_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "run.json"
            config.write_text(json.dumps({"model": {"name": "x"}, "surprise": True}), encoding="utf-8")
            result = self.run_cli("train", "--config", str(config), "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("unknown config key", result.stderr)

    def test_config_rejects_unknown_nested_keys_before_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "run.json"
            config.write_text(
                json.dumps(
                    {
                        "model": {"name": "x"},
                        "data": {"train": "data.jsonl"},
                        "training": {"output_dirr": "typo"},
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli("train", "--config", str(config), "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("training.output_dirr", result.stderr)

    def test_train_rejects_bad_data_before_attempting_platform_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "train.jsonl").write_text("not json\n", encoding="utf-8")
            config = project / "run.json"
            config.write_text(
                json.dumps(
                    {
                        "model": {"name": "x"},
                        "data": {"train": "train.jsonl"},
                        "training": {"method": "qlora"},
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli("train", "--project", str(project), "--config", str(config))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("invalid JSON", result.stdout)
            self.assertFalse((project / ".unsloth").exists())

    def test_skill_runs_from_copied_path_containing_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "copied skill"
            shutil.copytree(SKILL_ROOT, copied)
            result = subprocess.run(
                [sys.executable, str(copied / "scripts" / "unsloth_workflow.py"), "doctor", "--project", tmp],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_validate_data_flags_duplicate_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset = Path(tmp) / "dupes.jsonl"
            row = {"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]}
            dataset.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
            result = self.run_cli("validate-data", "--dataset", str(dataset))
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate", json.loads(result.stdout)["errors"][0])

    def test_alpaca_record_converts_to_chat_messages_for_evaluation(self):
        messages = messages_from_record(
            {"instruction": "Classify this", "input": "item", "output": "positive"}
        )
        self.assertEqual(messages[0]["role"], "user")
        self.assertIn("item", messages[0]["content"])
        self.assertEqual(messages[1], {"role": "assistant", "content": "positive"})

    def test_dataset_pair_rejects_train_eval_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            train = Path(tmp) / "train.jsonl"
            evaluation = Path(tmp) / "eval.jsonl"
            row = {"messages": [{"role": "user", "content": "x"}, {"role": "assistant", "content": "y"}]}
            train.write_text(json.dumps(row) + "\n", encoding="utf-8")
            evaluation.write_text(json.dumps(row) + "\n", encoding="utf-8")
            train_report, eval_report = validate_dataset_pair(train, evaluation)
            self.assertIn("train/eval overlap", train_report["errors"][0])
            self.assertIn("train/eval overlap", eval_report["errors"][0])


if __name__ == "__main__":
    unittest.main()
