import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import environment  # noqa: E402


class EnvironmentTests(unittest.TestCase):
    def test_setup_requires_gpu_before_creating_project_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            with (
                patch.object(environment.sys, "platform", "linux"),
                patch.object(environment, "doctor", return_value={"gpu_available": False, "gpu": []}),
                patch.object(environment.subprocess, "run") as run,
            ):
                with self.assertRaisesRegex(RuntimeError, "NVIDIA GPU"):
                    environment.setup(project)
            self.assertFalse((project / ".unsloth").exists())
            run.assert_not_called()

    def test_environment_health_rejects_missing_python_without_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            python = Path(tmp) / "missing-python"
            with patch.object(environment.subprocess, "run") as run:
                health = environment.environment_health(python)
            self.assertFalse(health["healthy"])
            self.assertIn("missing", health["error"])
            run.assert_not_called()

    def test_setup_rejects_an_incomplete_existing_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            python = project / ".unsloth" / "venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            with (
                patch.object(environment.sys, "platform", "linux"),
                patch.object(environment, "doctor", return_value={"gpu_available": True, "gpu": ["test GPU"]}),
                patch.object(environment.subprocess, "run") as run,
            ):
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    environment.setup(project)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
