"""Mocked-Hub tests for hub_publish.py: write-call ordering, refusal reasons,
recovery semantics, and receipt sanitization. No network access is performed."""
import copy
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
hp = importlib.import_module("hub_publish")
tam = importlib.import_module("test_artifact_manifest")
from test_artifact_manifest import STAGE_FILES, make_stage, valid_metadata  # noqa: E402

ACCOUNT = "rajivmehtapy"


class FakeApi:
    """Scriptable stand-in for huggingface_hub.HfApi; records every call."""

    def __init__(self, *, exists=False, remote_private=False, remote_files=None,
                 remote_sha="remote-head-sha", whoami_result=None,
                 fail_whoami=False, fail_upload=None, fail_model_info=False,
                 download_bytes=None):
        self.calls = []
        self.exists = exists
        self.remote_private = remote_private
        self.remote_files = remote_files or []
        self.remote_sha = remote_sha
        self.whoami_result = whoami_result or {"name": ACCOUNT, "orgs": []}
        self.fail_whoami = fail_whoami
        self.fail_upload = fail_upload
        self.fail_model_info = fail_model_info
        self.download_bytes = download_bytes if download_bytes is not None else dict(STAGE_FILES)

    def whoami(self):
        self.calls.append("whoami")
        if self.fail_whoami:
            raise RuntimeError("offline")
        return self.whoami_result

    def model_info(self, repo_id, repo_type="model"):
        self.calls.append(f"model_info:{repo_id}")
        if self.fail_model_info:
            raise RuntimeError("hub unreachable")
        if not self.exists:
            raise LookupError("not found")
        return SimpleNamespace(sha=self.remote_sha, private=self.remote_private)

    def list_repo_files(self, repo_id, repo_type="model"):
        self.calls.append(f"list_repo_files:{repo_id}")
        return list(self.remote_files)

    def create_repo(self, repo_id, private=True, exist_ok=False):
        self.calls.append(f"create_repo:{repo_id}:private={private}")
        self.exists = True
        self.remote_files = []

    def upload_folder(self, **kwargs):
        self.calls.append(f"upload_folder:{kwargs.get('repo_id')}:patterns={kwargs.get('allow_patterns')}")
        if self.fail_upload:
            raise RuntimeError(self.fail_upload)
        self.exists = True
        self.remote_files = sorted(kwargs.get("allow_patterns") or [])

    def hf_hub_download(self, repo_id, filename, repo_type="model", cache_dir=None):
        self.calls.append(f"hf_hub_download:{filename}")
        data = self.download_bytes.get(filename)
        if data is None:
            raise LookupError(filename)
        out = Path(cache_dir) / filename.replace("/", "_")
        out.write_bytes(data)
        return out


def verified_package(root: Path, **overrides) -> tuple[Path, dict]:
    stage = make_stage(root)
    metadata = valid_metadata()
    for key, value in overrides.items():
        section, _, field = key.partition("__")
        if field:
            metadata[section][field] = value
        else:
            metadata[section] = value
    manifest = tam.am.build_manifest(stage, metadata)
    return stage, manifest


class RefusalTests(unittest.TestCase):
    """No write call may happen before every prerequisite passes."""

    def _assert_refused_no_writes(self, api, receipt, needle):
        self.assertEqual(receipt["status"], "refused")
        self.assertTrue(any(needle in r for r in receipt["reasons"]), receipt["reasons"])
        self.assertFalse([c for c in api.calls if c.startswith(("create_repo", "upload_folder"))])

    def test_same_source_and_destination_refused_first(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi()
            r = hp.publish_package(stage, manifest, "Qwen/Qwen3-0.6B",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "destination equals source")
            self.assertNotIn("whoami", api.calls)

    def test_missing_credentials_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(fail_whoami=True)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "cannot establish Hub identity")

    def test_wrong_namespace_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi()
            r = hp.publish_package(stage, manifest, "someone-else/converted",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "not authorized")

    def test_license_not_clear_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(
                Path(td), license__status="needs-evidence")
            api = FakeApi()
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "publication requires")
            self.assertNotIn("whoami", api.calls)

    def test_failed_validation_gate_blocks_before_any_write(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            manifest["validation"]["phases"]["functional_smoke"]["state"] = "failed"
            api = FakeApi()
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "functional_smoke")
            self.assertNotIn("whoami", api.calls)

    def test_existing_repo_requires_create_false(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=True)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self._assert_refused_no_writes(api, r, "already exists")

    def test_visibility_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=True, remote_private=True)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="public", create=False, api=api)
            self._assert_refused_no_writes(api, r, "visibility mismatch")

    def test_file_conflicts_require_explicit_allow_replace(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=True, remote_files=["config.json"])
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=False, api=api)
            self._assert_refused_no_writes(api, r, "--allow-replace")

    def test_stale_expected_head_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=True, remote_sha="head-abc")
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=False,
                                   expected_head="head-000", api=api)
            self._assert_refused_no_writes(api, r, "stale expected head")
            self.assertTrue(r["remote_state_inspected"])

    def test_missing_repo_without_create_refused(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=False)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=False, api=api)
            self._assert_refused_no_writes(api, r, "--create not given")


class PublishTests(unittest.TestCase):
    def test_happy_path_publishes_and_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=False)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self.assertEqual(r["status"], "published", r)
            self.assertIn("create_repo:rajivmehtapy/converted:private=True", api.calls)
            self.assertTrue(any(c.startswith("upload_folder:") for c in api.calls))
            self.assertEqual(len([c for c in api.calls if c.startswith("upload_folder")]), 1)
            self.assertTrue(all(v == "verified" for v in r["files"].values()))
            self.assertEqual(r["commit"], "remote-head-sha")
            self.assertNotIn("hf_", json.dumps(r))
            # exact file set was uploaded — allow_patterns equals declared paths
            upload_call = next(c for c in api.calls if c.startswith("upload_folder"))
            self.assertIn(f"patterns={sorted(f['path'] for f in manifest['files'])}", upload_call)

    def test_interrupted_transfer_inspects_remote_without_retry(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=False, fail_upload="connection reset mid-transfer")
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self.assertEqual(r["status"], "error")
            self.assertIn("connection reset", r["error"])
            self.assertTrue(r["remote_state_inspected"])
            self.assertEqual(len([c for c in api.calls if c.startswith("upload_folder")]), 1)

    def test_lost_commit_response_reported_as_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            api = FakeApi(exists=False, fail_model_info=True)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self.assertEqual(r["status"], "unknown")
            self.assertIn("inspect remote before retrying", r["error"])

    def test_remote_content_mismatch_marks_unverified(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = verified_package(Path(td))
            corrupt = dict(STAGE_FILES)
            corrupt["config.json"] = b'{"model_type": "different"}'
            api = FakeApi(exists=False, download_bytes=corrupt)
            r = hp.publish_package(stage, manifest, f"{ACCOUNT}/converted",
                                   visibility="private", create=True, api=api)
            self.assertEqual(r["status"], "published-unverified")
            self.assertEqual(r["files"]["config.json"], "content-mismatch")
            self.assertEqual(r["files"]["LICENSE"], "verified")


if __name__ == "__main__":
    unittest.main()
