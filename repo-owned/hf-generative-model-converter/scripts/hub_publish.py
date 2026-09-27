#!/usr/bin/env python3
"""Controlled Hugging Face Hub publication for staged conversion packages.

Semantics enforced here (and asserted by tests/test_hub_publish.py):

- Credentials come exclusively from the local Hub configuration/environment.
  There is deliberately no token parameter.
- Prerequisites are checked in order and no write call is issued until all of
  them pass: manifest validity (including validation gates), license status,
  source/destination distinctness, namespace authorization, destination
  existence/visibility/conflicts/expected-head.
- A lost or interrupted transfer is never retried blindly: remote state is
  inspected and reported so the caller can decide.
- Remote verification streams and hashes files when no trustworthy server-side
  digest is available; an ETag is never treated as a SHA-256.
- The receipt contains no credentials and lives outside the staged inventory.

CLI:
    hub_publish.py publish --stage PATH --manifest PATH --repo-id NS/NAME
                           --visibility {private,public} [--create]
                           [--expected-head SHA] [--allow-replace]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_manifest import MANIFEST_NAME, sha256_bytes, sha256_file, validate_package  # noqa: E402


def _require_clean_manifest(stage: Path, manifest: dict) -> list[str]:
    return validate_package(Path(stage), manifest, require_gates=True)


def publish_package(
    stage: Path,
    manifest: dict,
    repo_id: str,
    *,
    visibility: str,
    create: bool,
    expected_head: str | None = None,
    allow_replace: bool = False,
    api=None,
) -> dict:
    """Publish a verified staged package; return a sanitized receipt dict."""
    stage = Path(stage)
    receipt: dict = {
        "status": "refused",
        "repo_id": repo_id,
        "visibility": visibility,
        "reasons": [],
        "files": {},
        "manifest_sha256": None,
        "commit": None,
        "url": f"https://huggingface.co/{repo_id}",
        "remote_state_inspected": False,
    }
    reasons = receipt["reasons"]

    # -- prerequisite 1: manifest + validation gates -------------------------
    errs = _require_clean_manifest(stage, manifest)
    if errs:
        reasons.extend(errs)
        return receipt

    # -- prerequisite 2: license --------------------------------------------
    if manifest["license"]["status"] != "clear":
        reasons.append(f"license status {manifest['license']['status']!r} is not publishable")
        return receipt

    # -- prerequisite 3: source/destination distinctness ---------------------
    if repo_id.strip("/").lower() == manifest["source"]["model_id"].strip("/").lower():
        reasons.append("destination equals source repository")
        return receipt

    declared = sorted(f["path"] for f in manifest["files"])
    receipt["manifest_sha256"] = None

    # -- prerequisite 4: identity/namespace (read-only call) -----------------
    if api is None:
        from huggingface_hub import HfApi  # deferred: keeps module import light
        api = HfApi()  # token resolution: env or stored config only
    try:
        me = api.whoami()
    except Exception as exc:
        reasons.append(f"cannot establish Hub identity (missing/invalid local credentials): {type(exc).__name__}")
        return receipt
    namespace = repo_id.split("/")[0]
    orgs = {o.get("name") for o in me.get("orgs", [])}
    if namespace != me.get("name") and namespace not in orgs:
        reasons.append(f"namespace {namespace!r} is not authorized for account {me.get('name')!r}")
        return receipt

    # -- prerequisite 5: destination inspection (read-only calls) ------------
    existing_sha = None
    try:
        info = api.model_info(repo_id)
        existing_sha = info.sha
    except Exception as exc:
        if not create:
            reasons.append(f"repository does not exist and --create not given: {type(exc).__name__}")
            return receipt
        info = None
    remote_files: list[str] | None = None
    if info is not None:
        if create:
            reasons.append("repository already exists; publish with --create omitted")
        is_private = bool(getattr(info, "private", False))
        if (visibility == "private") != is_private:
            reasons.append(
                f"visibility mismatch: remote is {'private' if is_private else 'public'}; "
                "existing visibility is preserved — request it explicitly"
            )
        try:
            remote_files = api.list_repo_files(repo_id, repo_type="model")
        except Exception as exc:
            reasons.append(f"cannot list remote files: {type(exc).__name__}")
        if remote_files is not None:
            conflicts = sorted(set(remote_files) & set(declared))
            if conflicts and not allow_replace:
                reasons.append("remote conflicts requiring explicit --allow-replace: " + ", ".join(conflicts))
        if expected_head is not None and existing_sha != expected_head:
            reasons.append(f"stale expected head: remote is {existing_sha}, expected {expected_head}")
        if reasons:
            receipt["remote_state_inspected"] = True
            return receipt

    # -- write phase ----------------------------------------------------------
    receipt["manifest_sha256"] = sha256_bytes(
        json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
    )
    try:
        if info is None:
            api.create_repo(repo_id, private=(visibility == "private"), exist_ok=False)
        api.upload_folder(
            repo_id=repo_id,
            repo_type="model",
            folder_path=str(stage),
            allow_patterns=declared,
            commit_message=f"Publish verified {manifest['recipe']['id']} package (manifest {receipt['manifest_sha256'][:12]})",
        )
    except Exception as exc:
        receipt["status"] = "error"
        receipt["error"] = f"transfer failed: {type(exc).__name__}: {exc}"
        try:
            info2 = api.model_info(repo_id)
            receipt["remote_state_inspected"] = True
            receipt["remote_state"] = {
                "exists": True,
                "commit": info2.sha,
                "files": sorted(api.list_repo_files(repo_id, repo_type="model")),
                "note": "inspect remote state before any retry; do not blind-retry a possibly-completed commit",
            }
        except Exception:
            receipt["remote_state_inspected"] = True
            receipt["remote_state"] = {"exists": False, "note": "remote not readable after failure"}
        return receipt

    # -- remote verification ---------------------------------------------------
    try:
        final = api.model_info(repo_id)
        receipt["commit"] = final.sha
        remote_files = api.list_repo_files(repo_id, repo_type="model")
    except Exception as exc:
        receipt["status"] = "unknown"
        receipt["error"] = f"commit response lost ({type(exc).__name__}); inspect remote before retrying"
        return receipt

    remote_set = set(remote_files or [])
    missing = sorted(set(declared) - remote_set)
    extra = sorted(remote_set - set(declared) - {MANIFEST_NAME})
    if not missing:
        verified_all = True
        with tempfile.TemporaryDirectory() as td:
            for rel in declared:
                try:
                    local = api.hf_hub_download(repo_id, rel, repo_type="model", cache_dir=td)
                    ok = sha256_file(Path(local)) == _declared_sha(manifest, rel)
                except Exception as exc:
                    ok = False
                    receipt["files"][rel] = f"verification error: {type(exc).__name__}"
                else:
                    receipt["files"][rel] = "verified" if ok else "content-mismatch"
                verified_all &= ok
        receipt["status"] = "published" if verified_all else "published-unverified"
    else:
        receipt["status"] = "published-unverified"
        receipt["error"] = f"remote missing files: {', '.join(missing)}"
    if extra:
        receipt["extra_remote_files"] = extra
    return receipt


def _declared_sha(manifest: dict, rel: str) -> str:
    for f in manifest["files"]:
        if f["path"] == rel:
            return f["sha256"]
    raise KeyError(rel)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guarded Hugging Face Hub publication")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("publish")
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--repo-id", required=True)
    p.add_argument("--visibility", choices=("private", "public"), required=True)
    p.add_argument("--create", action="store_true")
    p.add_argument("--expected-head", default=None)
    p.add_argument("--allow-replace", action="store_true")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text())
    receipt = publish_package(
        args.stage, manifest, args.repo_id,
        visibility=args.visibility, create=args.create,
        expected_head=args.expected_head, allow_replace=args.allow_replace,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["status"] == "published" else 1


if __name__ == "__main__":
    raise SystemExit(_main())
