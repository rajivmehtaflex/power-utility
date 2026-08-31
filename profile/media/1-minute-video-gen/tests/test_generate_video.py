from __future__ import annotations

import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch


SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "generate_video.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_video", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load generate_video.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload, content=b""):
        self.payload = payload
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.payload = None

    def post(self, _url, json, timeout):
        self.payload = json
        return FakeResponse({"id": "job-1", "polling_url": "https://example.test/job-1"})

    def get(self, url, timeout):
        if url.endswith("job-1"):
            return FakeResponse({"status": "completed", "unsigned_urls": ["https://example.test/content"]})
        return FakeResponse({}, content=b"video")


class GenerateVideoTests(unittest.TestCase):
    def test_skill_has_portable_spec_metadata(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("license: MIT", text)
        self.assertIn("compatibility:", text)
        self.assertIn("metadata:", text)

    def test_request_uses_selected_resolution_and_audio(self):
        module = load_module()
        session = FakeSession()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = pathlib.Path(temp_dir) / "output.mp4"
            with patch.object(module.time, "sleep", return_value=None):
                module.submit_and_download(
                    session=session,
                    model="bytedance/seedance-2.0-mini",
                    prompt="A continuous road journey",
                    duration=15,
                    resolution="480p",
                    generate_audio=False,
                    output_path=output_path,
                )

            self.assertEqual(session.payload["resolution"], "480p")
            self.assertFalse(session.payload["generate_audio"])
            self.assertEqual(output_path.read_bytes(), b"video")


if __name__ == "__main__":
    unittest.main()
