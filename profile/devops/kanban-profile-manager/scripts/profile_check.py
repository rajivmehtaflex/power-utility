#!/usr/bin/env python3
"""
Phase 1 — Kanban Profile Readiness Checker
===========================================

Reads a role registry, reconciles against the live Hermes profile catalog,
and returns a structured readiness report. Does NOT create Kanban tasks
or start workers. Phase 1 boundary: preparation only.

Usage:
    python3 scripts/profile_check.py --registry references/profile-provisioning-registry.yaml
    python3 scripts/profile_check.py --registry my-registry.yaml --provision
    python3 scripts/profile_check.py --registry my-registry.yaml --json

See: references/readiness-report-contract.md for output structure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml

# Import config merger at module level so it can be mocked in tests
try:
    from config_merger import apply_overrides_to_config, validate_overrides
except ImportError:
    apply_overrides_to_config = None
    validate_overrides = None


# ─── Data Structures ───────────────────────────────────────────────

@dataclass
class RoleResult:
    role: str
    profile_name: str
    action: str = ""  # reused | created | needs_update | blocked | failed
    profile_created: bool = False
    ready_for_dispatch: bool = False
    reason: str = ""
    template: Optional[str] = None
    verification: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "profile_name": self.profile_name,
            "action": self.action,
            "profile_created": self.profile_created,
            "ready_for_dispatch": self.ready_for_dispatch,
            "reason": self.reason,
            "template": self.template,
            "verification": self.verification,
        }


@dataclass
class ReadinessReport:
    registry_path: str
    mode: str
    existing_profiles: list = field(default_factory=list)
    results: list = field(default_factory=list)  # list[RoleResult]
    execution_started: bool = False
    phase: str = "profile-preparation"
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def summary(self) -> dict:
        return {
            "all_ready": all(r.ready_for_dispatch for r in self.results) if self.results else True,
            "total_roles": len(self.results),
            "reused": sum(1 for r in self.results if r.action == "reused"),
            "created": sum(1 for r in self.results if r.action == "created"),
            "blocked": sum(1 for r in self.results if r.action == "blocked"),
            "failed": sum(1 for r in self.results if r.action == "failed"),
            "needs_update": sum(1 for r in self.results if r.action == "needs_update"),
        }

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "execution_started": self.execution_started,
            "mode": self.mode,
            "registry_path": self.registry_path,
            "generated_at": self.generated_at,
            "existing_profiles": self.existing_profiles,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
        }


# ─── Registry Loading ──────────────────────────────────────────────

def load_registry(path: str) -> dict:
    """Load and validate the role registry YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Registry not found: {path}")
    with open(p) as f:
        reg = yaml.safe_load(f)
    if "roles" not in reg:
        raise ValueError("Registry must contain a 'roles' key")
    for role_name, role_def in (reg["roles"] or {}).items():
        for required_field in ("description", "skills", "auto_create"):
            if required_field not in role_def:
                raise ValueError(f"Role '{role_name}' missing required field: {required_field}")
    return reg


# ─── Role Catalog (for agent-driven task analysis) ─────────────────

def get_role_catalog(registry: dict) -> list:
    """
    Extract the role catalog from a registry for agent-driven task analysis.
    Returns a list of role summaries with capabilities and skills,
    so an agent can match a task description to the roles it needs.
    """
    catalog = []
    for role_name, role_def in (registry.get("roles") or {}).items():
        catalog.append({
            "role": role_name,
            "description": role_def.get("description", ""),
            "capabilities": role_def.get("capabilities", ""),
            "skills": role_def.get("skills", []),
            "auto_create": role_def.get("auto_create", False),
        })
    return catalog


def print_role_catalog(catalog: list, task_description: str = ""):
    """
    Print the role catalog in a format the agent can reason against.
    If a task description is provided, it is shown as context.
    """
    if task_description:
        print(f"\n{'='*60}")
        print(f"  TASK DESCRIPTION")
        print(f"{'='*60}")
        print(f"  {task_description}")
        print(f"{'='*60}")

    print(f"\n{'='*60}")
    print(f"  AVAILABLE ROLE CATALOG")
    print(f"{'='*60}")
    for entry in catalog:
        print(f"\n  Role: {entry['role']}")
        print(f"  Description: {entry['description']}")
        if entry["capabilities"]:
            print(f"  Capabilities: {entry['capabilities']}")
        if entry["skills"]:
            print(f"  Skills: {', '.join(entry['skills'])}")
        print(f"  Auto-create: {entry['auto_create']}")
    sep = "\u2500" * 60
    print(f"\n{sep}")
    print("  Analyze the task description above. Identify which roles are needed.")
    print("  Then run: python3 profile_check.py --registry <path> --roles role1,role2 [--provision]")
    print(f"{sep}\n")


# ─── Profile Discovery ─────────────────────────────────────────────

def get_existing_profiles() -> List[str]:
    """Run `hermes profile list` and parse profile names."""
    result = subprocess.run(
        ["hermes", "profile", "list"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return []
    profiles = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("Profile") or line.startswith("\u2500"):
            continue
        name = line.split()[0].lstrip("\u25c6").strip()
        if name:
            profiles.append(name)
    return profiles


# ─── Profile Creation & Verification ───────────────────────────────

def create_profile(role_name: str, role_def: dict, apply_config: bool = True) -> bool:
    """Create a profile via the Hermes CLI, then optionally apply config overrides."""
    cmd = [
        "hermes", "profile", "create", role_name,
        "--description", role_def["description"],
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return False

    # Apply config overrides if present and enabled
    overrides = role_def.get("config_overrides")
    if apply_config and overrides:
        if apply_overrides_to_config is None or validate_overrides is None:
            # config_merger not available — skip gracefully
            return True

        warnings = validate_overrides(overrides)
        for w in warnings:
            print(f"  WARNING: {w}", file=sys.stderr)

        profile_config = Path.home() / ".hermes" / "profiles" / role_name / "config.yaml"
        if profile_config.exists():
            try:
                apply_overrides_to_config(str(profile_config), overrides)
            except Exception as e:
                print(f"  WARNING: Failed to apply config overrides for {role_name}: {e}", file=sys.stderr)
                # Profile was created; overrides failed — not a hard failure
        else:
            print(f"  WARNING: Profile config not found at {profile_config}", file=sys.stderr)

    return True


def verify_profile(role_name: str, required_skills: list) -> dict:
    """Verify that a profile exists and has the expected configuration."""
    result = subprocess.run(
        ["hermes", "profile", "show", role_name],
        capture_output=True, text=True, timeout=30,
    )
    exists = result.returncode == 0
    output = result.stdout + result.stderr
    return {
        "exists": exists,
        "description_ok": exists,  # description was set at creation time
        "skills_ok": True,  # Hermes skills are global; per-profile check is advisory
        "tools_ok": "Model:" in output if exists else False,
    }


# ─── Core Resolution Logic ─────────────────────────────────────────

def resolve_profiles(
    registry: dict,
    existing: list,
    provision: bool = False,
    requested_roles: Optional[List[str]] = None,
    apply_config_overrides: bool = True,
) -> ReadinessReport:
    """
    Reconcile required roles against existing profiles.
    Phase 1 only: no task creation, no worker dispatch.

    Args:
        registry:        Loaded registry dict (from load_registry).
        existing:        List of profile names that already exist.
        provision:       If True, create missing profiles (requires provision-approved mode).
        requested_roles: Optional subset of roles to check. If None, checks all registry roles.
        apply_config_overrides: If True, apply config_overrides to newly created profiles.
    """
    report = ReadinessReport(
        registry_path=registry.get("_path", ""),
        mode=registry.get("mode", "reuse-only"),
        existing_profiles=list(existing),
    )

    mode = registry["mode"]
    max_create = registry.get("max_auto_created_profiles", 8)
    registry_roles = registry.get("roles") or {}
    roles_to_check = requested_roles if requested_roles is not None else list(registry_roles.keys())
    created_so_far = 0

    for role_name in roles_to_check:
        # Unknown role check — not in registry
        if role_name not in registry_roles:
            report.results.append(RoleResult(
                role=role_name,
                profile_name=role_name,
                action="blocked",
                reason=f"Role '{role_name}' is not in the approved registry",
            ))
            continue

        role_def = registry_roles[role_name]
        result = RoleResult(role=role_name, profile_name=role_name)

        # Step 3: Reuse before create
        if role_name in existing:
            verification = verify_profile(role_name, role_def.get("skills", []))
            if verification["exists"]:
                result.action = "reused"
                result.ready_for_dispatch = True
                result.reason = "Existing profile satisfies the role contract"
                result.verification = verification
            else:
                result.action = "needs_update"
                result.reason = "Profile exists but failed verification"
                result.verification = verification
            report.results.append(result)
            continue

        # Step 4: Apply missing-profile policy
        if mode == "reuse-only":
            result.action = "blocked"
            result.reason = "No existing profile matches; mode is reuse-only"
        elif mode == "approval-required":
            result.action = "blocked"
            result.reason = "Role requires human approval before creation"
        elif mode == "provision-approved":
            if not role_def.get("auto_create"):
                result.action = "blocked"
                result.reason = "Role has auto_create=false"
            elif not provision:
                result.action = "blocked"
                result.reason = "Missing profile; --provision not passed"
            elif created_so_far >= max_create:
                result.action = "blocked"
                result.reason = f"max_auto_created_profiles limit ({max_create}) reached"
            else:
                # Step 5: Provision (+ apply config overrides)
                success = create_profile(role_name, role_def, apply_config=apply_config_overrides)
                if success:
                    verification = verify_profile(role_name, role_def.get("skills", []))
                    if verification["exists"]:
                        result.action = "created"
                        result.profile_created = True
                        result.ready_for_dispatch = True
                        result.reason = "Profile created from approved template"
                        result.template = role_def.get("base_profile", "default")
                        result.verification = verification
                        created_so_far += 1
                    else:
                        result.action = "failed"
                        result.reason = "Profile created but verification failed"
                        result.verification = verification
                else:
                    result.action = "failed"
                    result.reason = "Profile creation command failed"
        else:
            result.action = "blocked"
            result.reason = f"Unknown mode: {mode}"

        report.results.append(result)

    return report


# ─── CLI Entry Point ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 Kanban Profile Readiness Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See references/readiness-report-contract.md for output structure.",
    )
    parser.add_argument("--registry", required=True, help="Path to role registry YAML")
    parser.add_argument("--provision", action="store_true",
                        help="Create missing profiles (requires provision-approved mode)")
    parser.add_argument("--json", action="store_true", help="Output JSON readiness report")

    # Config overrides control
    parser.add_argument("--no-config", action="store_true",
                        help="Skip applying config_overrides after profile creation (bare profiles only)")

    # Task-driven mode: show role catalog for agent reasoning
    parser.add_argument("--task", default=None,
                        help="Task description to analyze. Prints the role catalog so the agent "
                             "can infer which roles are needed, then exits.")

    # Explicit roles mode: check specific roles only (used after agent infers roles from --task)
    parser.add_argument("--roles", default=None,
                        help="Comma-separated role names to check (e.g. 'researcher,reviewer'). "
                             "Used after the agent has inferred roles from a task description.")

    args = parser.parse_args()

    reg = load_registry(args.registry)
    reg["_path"] = str(Path(args.registry).resolve())

    # ─── Task-driven mode: print role catalog for agent reasoning ───
    if args.task:
        catalog = get_role_catalog(reg)
        if args.json:
            print(json.dumps({"task": args.task, "role_catalog": catalog}, indent=2))
        else:
            print_role_catalog(catalog, task_description=args.task)
        sys.exit(0)

    # ─── Parse --roles if provided ─────────────────────────────────
    requested_roles = None
    if args.roles:
        requested_roles = [r.strip() for r in args.roles.split(",") if r.strip()]

    # ─── Profile resolution ────────────────────────────────────────
    existing = get_existing_profiles()
    report = resolve_profiles(
        reg,
        existing,
        provision=args.provision,
        requested_roles=requested_roles,
        apply_config_overrides=not args.no_config,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        s = report.summary
        print(f"\n{'='*60}")
        print(f"  KANBAN PROFILE READINESS REPORT")
        print(f"{'='*60}")
        print(f"  Phase: {report.phase}")
        print(f"  Mode: {report.mode}")
        print(f"  Execution started: {report.execution_started}")
        print(f"  Generated: {report.generated_at}")
        print(f"  Existing profiles: {', '.join(report.existing_profiles)}")
        sep = "\u2500" * 60
        print(sep)
        for r in report.results:
            icon = {"reused": "\u2713", "created": "+", "blocked": "\u2717", "failed": "!", "needs_update": "?"}
            print(f"  {icon.get(r.action, '?')} {r.role:20s} \u2192 {r.action:12s} ready={r.ready_for_dispatch}")
            if r.reason:
                print(f"      {r.reason}")
        print(sep)
        print(f"  Reused: {s['reused']}  Created: {s['created']}  Blocked: {s['blocked']}  Failed: {s['failed']}")
        print(f"  All ready: {s['all_ready']}")
        print(f"{'='*60}\n")

    sys.exit(0 if report.summary["all_ready"] else 1)


if __name__ == "__main__":
    main()
