"""Meaningful tests for artifact_manifest.py: exact inventories, tamper detection,
unsafe paths, secrets, schema/status failures, nonrecursive manifest, CLI round-trip."""
import copy
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
am = importlib.import_module("artifact_manifest")

STAGE_FILES = {
    "model-card.md": b"# card\n",
    "LICENSE": b"Apache-2.0\n",
    "qwen3-0.6b-f16.gguf": b"\x00\x01GGUF-fake-payload",
    "config.json": b'{"model_type": "qwen3"}',
    "tokenizer.json": b"{}",
}


def valid_metadata():
    return {
        "source": {
            "model_id": "Qwen/Qwen3-0.6B",
            "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
            "architecture": "Qwen3ForCausalLM",
            "task": "text-generation",
            "license": "apache-2.0",
        },
        "recipe": {
            "id": "gguf-qwen3-0.6b-linux-x64-cpu",
            "revision": 1,
            "target": "gguf",
            "required_files": ["config.json", "tokenizer.json"],
        },
        "toolchain": {
            "name": "llama.cpp",
            "revision": "7fe450e19305b828c199d602c23a8337aaa1f03b",
            "build_key": "198232c63ac3c736",
            "dependency_locks": [
                {"name": "uv.lock", "sha256": "87" * 32}
            ],
            "binary_exceptions": [],
        },
        "build_host": {"os": "Ubuntu 24.04.5 LTS", "arch": "x86_64", "interpreter": "CPython 3.12.3"},
        "deployment": {"platform": "linux-x86_64", "execution": "cpu", "accelerator": "none-verified"},
        "profile": {
            "outtype": "f16", "quantization": "none", "context_length": 4096, "batch": 1,
            "sampling": "greedy", "seed": 42, "max_new_tokens": 32, "chat_template": "preserved",
        },
        "license": {"status": "clear", "references": ["LICENSE in stage"]},
        "validation": {
            "fixtures": [
                {"id": "fixture-1", "sha256": "aa" * 32},
                {"id": "fixture-2", "sha256": "bb" * 32},
                {"id": "fixture-3", "sha256": "cc" * 32, "near_limit": True},
            ],
            "generation": {"sampling": "greedy", "seed": 42, "max_new_tokens": 32, "context_length": 4096},
            "runtime": {"name": "llama-cli", "version": "0.5.0-dev commit 7fe450e", "backend": "cpu"},
            "phases": {
                "functional_smoke": {"state": "passed"},
                "numerical_fidelity": {"state": "passed", "metric": "token-jaccard", "threshold": 0.5, "measured": 0.83},
                "staged_reload": {"state": "passed"},
            },
            "limitations": ["CPU-only verification"],
        },
    }


def make_stage(root: Path, files: dict[str, bytes] | None = None) -> Path:
    stage = root / "stage"
    stage.mkdir(parents=True)
    for rel, data in (files or STAGE_FILES).items():
        p = stage / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return stage


class BuildTests(unittest.TestCase):
    def test_exact_inventory_is_sorted_and_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stage = make_stage(root)
            m1 = am.build_manifest(stage, valid_metadata())
            m2 = am.build_manifest(stage, valid_metadata())
            self.assertEqual(m1, m2)
            self.assertEqual([f["path"] for f in m1["files"]], sorted(STAGE_FILES))
            self.assertNotIn(am.MANIFEST_NAME, [f["path"] for f in m1["files"]])
            for f in m1["files"]:
                self.assertEqual(f["size"], len(STAGE_FILES[f["path"]]))
                self.assertEqual(f["sha256"], am.sha256_bytes(STAGE_FILES[f["path"]]))

    def test_rejects_symlink_in_stage(self):
        with tempfile.TemporaryDirectory() as td:
            stage = make_stage(Path(td))
            (stage / "link.json").symlink_to(stage / "config.json")
            with self.assertRaisesRegex(am.ManifestError, "non-regular file"):
                am.build_manifest(stage, valid_metadata())

    def test_rejects_secret_looking_metadata(self):
        bad = valid_metadata()
        bad["deployment"]["notes"] = "deploy with hf_FAKE0123456789abcdef"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(am.ManifestError, "secret-looking"):
                am.build_manifest(make_stage(Path(td)), bad)

    def test_rejects_forbidden_key(self):
        bad = valid_metadata()
        bad["deployment"]["api_key"] = "rotate-me"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(am.ManifestError, "forbidden field"):
                am.build_manifest(make_stage(Path(td)), bad)

    def test_rejects_schema_violation(self):
        bad = valid_metadata()
        del bad["license"]
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(am.ManifestError, "schema"):
                am.build_manifest(make_stage(Path(td)), bad)


class VerifyTests(unittest.TestCase):
    def _built(self, root: Path):
        stage = make_stage(root)
        manifest = am.build_manifest(stage, valid_metadata())
        return stage, manifest

    def test_verify_clean_package_passes(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            self.assertEqual(am.validate_package(stage, manifest), [])

    def test_altered_hash_detected(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            (stage / "config.json").write_bytes(b'{"model_type": "tampered"}')
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("sha256 mismatch: config.json" in e for e in errors))

    def test_missing_required_sidecar_detected(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            (stage / "tokenizer.json").unlink()
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("missing staged file: tokenizer.json" in e for e in errors))
            self.assertTrue(any("recipe required file absent" in e for e in errors))

    def test_unexpected_source_weights_detected(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            (stage / "leaked-original.safetensors").write_bytes(b"weights")
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("unexpected file in stage: leaked-original.safetensors" in e for e in errors))

    def test_escaping_and_absolute_paths_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            manifest["files"].append({"path": "../outside.gguf", "size": 1, "sha256": "ab" * 32})
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("unsafe path in manifest: ../outside.gguf" in e for e in errors))
            manifest["files"][-1]["path"] = "/etc/passwd"
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("unsafe path in manifest: /etc/passwd" in e for e in errors))

    def test_symlinked_stage_file_detected_after_build(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            target = stage / "config.json"
            real = stage / "real-config.json"
            real.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(real)
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("non-regular file in stage: config.json" in e for e in errors))

    def test_manifest_listing_itself_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            manifest["files"].append({"path": am.MANIFEST_NAME, "size": 2, "sha256": "cd" * 32})
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("must not be listed in its own files[]" in e for e in errors))

    def test_failed_gate_blocks_and_skip_flag_allows(self):
        with tempfile.TemporaryDirectory() as td:
            stage, manifest = self._built(Path(td))
            manifest["validation"]["phases"]["staged_reload"]["state"] = "failed"
            errors = am.validate_package(stage, manifest)
            self.assertTrue(any("staged_reload" in e for e in errors))
            self.assertEqual(am.validate_package(stage, manifest, require_gates=False), [])

    def test_paths_with_spaces_supported(self):
        files = dict(STAGE_FILES)
        files["converted models/my model.gguf"] = files.pop("qwen3-0.6b-f16.gguf")
        with tempfile.TemporaryDirectory() as td:
            stage = make_stage(Path(td), files)
            manifest = am.build_manifest(stage, valid_metadata())
            self.assertEqual(am.validate_package(stage, manifest), [])

    def test_cli_roundtrip_from_foreign_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stage = make_stage(root)
            meta = root / "meta.json"
            meta.write_text(json.dumps(valid_metadata()))
            out = root / am.MANIFEST_NAME
            for cwd in (root, Path("/")):
                r = subprocess.run(
                    [sys.executable, str(SCRIPTS / "artifact_manifest.py"), "build",
                     "--stage", str(stage), "--metadata", str(meta), "--out", str(out)],
                    capture_output=True, text=True, cwd=cwd,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
            (stage / "config.json").write_bytes(b"tampered")
            r = subprocess.run(
                [sys.executable, str(SCRIPTS / "artifact_manifest.py"), "verify",
                 "--stage", str(stage), "--manifest", str(out)],
                capture_output=True, text=True, cwd=Path("/"),
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("sha256 mismatch: config.json", r.stdout)


if __name__ == "__main__":
    unittest.main()
