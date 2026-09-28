#!/usr/bin/env python3
"""Deterministic artifact manifest build/verify for staged conversion packages.

Manifest schema version 1 lives in ../assets/manifest.schema.json. The manifest
never contains its own hash: the external publication receipt records the
manifest hash together with the remote commit.

CLI:
    artifact_manifest.py build --stage PATH --metadata PATH --out PATH
    artifact_manifest.py verify --stage PATH --manifest PATH [--skip-gates]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "assets" / "manifest.schema.json"
MANIFEST_NAME = "artifact-manifest.json"
_CHUNK = 1 << 20

_SECRET_KEY_RE = re.compile(
    r"(_|^)(access|auth|api|hf|hub|refresh|session|login)_?tokens?(_|$)"  # *_token, but not max_new_tokens
    r"|^tokens?$"
    r"|secret|password|passwd|authorization|credential|private[_-]?key|(^|_)api[_-]?keys?(_|$)",
    re.I)
_SECRET_VALUE_RE = re.compile(r"\bhf_[A-Za-z0-9]{16,}\b|signature=|X-Amz-|Bearer\s")
_GATE_PASS = "passed"


class ManifestError(Exception):
    """Raised by build when the manifest cannot be produced."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_rel(rel: str) -> bool:
    if not rel or rel == MANIFEST_NAME:
        return False
    p = PurePosixPath(rel)
    if p.is_absolute() or "\\" in rel or rel.startswith("~"):
        return False
    parts = p.parts
    if any(part in ("..", ".") for part in parts):
        return False
    # huggingface_hub download residue: created inside local_dir by hf_hub_download and never a
    # legitimate package member (observed in the p11 round)
    if any(part == ".cache" for part in parts):
        return False
    return True


def _iter_stage_files(stage: Path):
    """Yield (relative_posix_path, absolute_path) for regular, non-symlink files."""
    for root, dirs, names in os.walk(stage):
        for d in list(dirs):
            if (Path(root) / d).is_symlink():
                raise ManifestError(f"symlinked directory not allowed in stage: {d}")
        for n in names:
            p = Path(root) / n
            rel = p.relative_to(stage).as_posix()
            yield rel, p


def _validate_schema(manifest: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        return [f"jsonschema unavailable: {exc}"]
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    return [f"schema: {'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
            for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))]


def _scan_secrets(node, path="") -> list[str]:
    """Reject secret-looking keys/values anywhere in the manifest tree."""
    errors: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{path}.{k}" if path else str(k)
            # the schema mandates `authorization` on binary-exception entries (who authorized the
            # declared input); it is a policy statement, not a credential
            is_declared_exception = here.startswith("toolchain.binary_exceptions[") and k == "authorization"
            if not is_declared_exception and _SECRET_KEY_RE.search(str(k)):
                errors.append(f"forbidden field: {here}")
            errors += _scan_secrets(v, here)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            errors += _scan_secrets(v, f"{path}[{i}]")
    elif isinstance(node, str):
        if _SECRET_VALUE_RE.search(node):
            errors.append(f"secret-looking value at {path}")
    return errors


def _collect_stage_files(stage: Path) -> list[dict]:
    files = []
    for rel, p in _iter_stage_files(stage):
        if rel == MANIFEST_NAME:
            continue
        if not _safe_rel(rel):
            raise ManifestError(f"unsafe path in stage: {rel}")
        if p.is_symlink() or not p.is_file():
            raise ManifestError(f"non-regular file in stage: {rel}")
        files.append({"path": rel, "size": p.stat().st_size, "sha256": sha256_file(p)})
    return sorted(files, key=lambda f: f["path"])


def build_manifest(stage: Path, metadata: dict) -> dict:
    """Inventory the stage and merge metadata into a schema-valid manifest."""
    manifest = dict(metadata)
    manifest["schema_version"] = 1
    manifest["files"] = _collect_stage_files(stage)
    errors = _validate_schema(manifest) + _scan_secrets(manifest)
    if errors:
        raise ManifestError("\n".join(errors))
    return manifest


def validate_package(stage: Path, manifest: dict, *, require_gates: bool = True) -> list[str]:
    """Return a list of human-readable errors; empty list means the package is valid.

    Checks: schema, secret-free content, safe relative paths, nonrecursive
    manifest (files[] never lists the manifest itself), exact file set vs the
    stage, per-file size and SHA-256, recipe-declared required files, license
    status, and (optionally) required validation gates marked passed.
    """
    stage = Path(stage)
    errors: list[str] = []
    errors += _validate_schema(manifest)
    errors += _scan_secrets(manifest)

    declared_paths = [f.get("path", "") for f in manifest.get("files", [])]
    if MANIFEST_NAME in declared_paths:
        errors.append(f"{MANIFEST_NAME} must not be listed in its own files[]; the publication receipt records the manifest hash")
    for rel in declared_paths:
        if not _safe_rel(rel):
            errors.append(f"unsafe path in manifest: {rel}")

    actual: dict[str, Path] = {}
    try:
        for rel, p in _iter_stage_files(stage):
            if rel == MANIFEST_NAME:
                continue
            if p.is_symlink() or not p.is_file():
                errors.append(f"non-regular file in stage: {rel}")
                continue
            actual[rel] = p
    except ManifestError as exc:
        errors.append(str(exc))

    declared: dict[str, dict] = {f["path"]: f for f in manifest.get("files", []) if _safe_rel(f.get("path", ""))}
    for rel in sorted(set(declared) - set(actual)):
        errors.append(f"missing staged file: {rel}")
    for rel in sorted(set(actual) - set(declared)):
        errors.append(f"unexpected file in stage: {rel}")
    for rel in sorted(set(declared) & set(actual)):
        entry = declared[rel]
        p = actual[rel]
        if entry.get("size") != p.stat().st_size:
            errors.append(f"size mismatch: {rel}")
        if entry.get("sha256") != sha256_file(p):
            errors.append(f"sha256 mismatch: {rel}")

    for required in manifest.get("recipe", {}).get("required_files", []):
        if required not in actual:
            errors.append(f"recipe required file absent from package: {required}")
    if not any(rel == "model-card.md" for rel in declared):
        errors.append("required asset missing: model-card.md")

    status = manifest.get("license", {}).get("status")
    if status != "clear":
        errors.append(f"license status is {status!r}; publication requires 'clear'")

    phases = manifest.get("validation", {}).get("phases", {})
    if require_gates:
        for gate in ("functional_smoke", "staged_reload"):
            state = phases.get(gate, {}).get("state")
            if state != _GATE_PASS:
                errors.append(f"validation gate {gate} is {state!r}; required: '{_GATE_PASS}'")
    return errors


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/verify staged-package artifact manifests")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="inventory a stage directory into a manifest")
    p_build.add_argument("--stage", type=Path, required=True)
    p_build.add_argument("--metadata", type=Path, required=True)
    p_build.add_argument("--out", type=Path, required=True)

    p_verify = sub.add_parser("verify", help="verify a stage against its manifest")
    p_verify.add_argument("--stage", type=Path, required=True)
    p_verify.add_argument("--manifest", type=Path, required=True)
    p_verify.add_argument("--skip-gates", action="store_true",
                          help="structural check only; do not require passed validation gates")

    args = parser.parse_args(argv)
    if args.cmd == "build":
        try:
            metadata = json.loads(args.metadata.read_text())
            manifest = build_manifest(args.stage, metadata)
        except (ManifestError, OSError, json.JSONDecodeError) as exc:
            print(f"build failed: {exc}", file=sys.stderr)
            return 1
        args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"manifest written: {args.out} ({len(manifest['files'])} files)")
        return 0

    try:
        manifest = json.loads(args.manifest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"verify failed: {exc}", file=sys.stderr)
        return 1
    errors = validate_package(args.stage, manifest, require_gates=not args.skip_gates)
    if errors:
        print("verify failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"package verified: {len(manifest['files'])} files, all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
