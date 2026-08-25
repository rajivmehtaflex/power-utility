"""Tests for the Phase 1 profile readiness checker script.

These tests use fixture registries and mock subprocess calls so they run
without a live Hermes installation or real profile mutations.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Make the script importable
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPT_DIR)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# ─── Helpers ───────────────────────────────────────────────────────

def load_fixture(name):
    path = os.path.join(FIXTURES, name)
    with open(path) as f:
        return yaml.safe_load(f)


def mock_profile_list(names):
    """Build a fake `hermes profile list` stdout."""
    lines = ["Profile          Model     Gateway", "\u2500" * 40]
    for n in names:
        lines.append(f"  {n}         test      running")
    return "\n".join(lines)


def mock_profile_show(name):
    """Build a fake `hermes profile show` stdout."""
    return f"Profile: {name}\nModel: test-model\nGateway: running\nSkills: 0"


# ─── Test: Registry Loading ────────────────────────────────────────

class TestRegistryLoading:
    def test_loads_sample_registry(self):
        from profile_check import load_registry
        reg = load_registry(os.path.join(FIXTURES, "sample-registry.yaml"))
        assert "roles" in reg
        assert "researcher" in reg["roles"]
        assert reg["mode"] == "provision-approved"

    def test_loads_empty_registry(self):
        from profile_check import load_registry
        reg = load_registry(os.path.join(FIXTURES, "empty-registry.yaml"))
        assert reg["roles"] == {}

    def test_rejects_missing_file(self):
        from profile_check import load_registry
        with pytest.raises(FileNotFoundError):
            load_registry("/nonexistent/path.yaml")

    def test_validates_required_fields(self):
        from profile_check import load_registry
        # Write a temp invalid registry missing 'auto_create'
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"mode": "reuse-only", "roles": {"bad-role": {"description": "x", "skills": []}}}, f)
            tmp_path = f.name
        with pytest.raises(ValueError, match="auto_create"):
            load_registry(tmp_path)
        os.unlink(tmp_path)


# ─── Test: Profile Discovery ───────────────────────────────────────

class TestProfileDiscovery:
    @patch("profile_check.subprocess.run")
    def test_parses_profile_names(self, mock_run):
        from profile_check import get_existing_profiles
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_profile_list(["default", "researcher", "reviewer"]),
        )
        profiles = get_existing_profiles()
        assert "default" in profiles
        assert "researcher" in profiles
        assert "reviewer" in profiles

    @patch("profile_check.subprocess.run")
    def test_empty_on_cli_failure(self, mock_run):
        from profile_check import get_existing_profiles
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert get_existing_profiles() == []


# ─── Test: Reuse-Only Mode ─────────────────────────────────────────

class TestReuseOnlyMode:
    """Article test case: 'All profiles already exist -> reuse-only, no creation'."""

    def _registry(self):
        reg = load_fixture("sample-registry.yaml")
        reg["mode"] = "reuse-only"
        return reg

    @patch("profile_check.subprocess.run")
    def test_all_exist_returns_reused(self, mock_run):
        from profile_check import resolve_profiles
        reg = self._registry()

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_list(["default", "researcher", "analyst", "reviewer"]))
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        report = resolve_profiles(reg, existing=["default", "researcher", "analyst", "reviewer"])
        assert report.summary["all_ready"] is True
        assert report.summary["reused"] == 3
        assert report.summary["created"] == 0
        assert report.summary["blocked"] == 0

    @patch("profile_check.subprocess.run")
    def test_one_missing_is_blocked(self, mock_run):
        """Article test case: missing profile in reuse-only -> blocked."""
        from profile_check import resolve_profiles
        reg = self._registry()

        mock_run.return_value = MagicMock(
            returncode=0, stdout=mock_profile_list(["default", "researcher", "analyst"])
        )
        # reviewer is missing
        report = resolve_profiles(reg, existing=["default", "researcher", "analyst"])
        assert report.summary["all_ready"] is False
        assert report.summary["blocked"] == 1
        reviewer_result = [r for r in report.results if r.role == "reviewer"][0]
        assert reviewer_result.action == "blocked"


# ─── Test: Provision-Approved Mode ─────────────────────────────────

class TestProvisionApprovedMode:
    """Article test case: 'One profile missing with approved template -> create exactly one'."""

    @patch("profile_check.subprocess.run")
    def test_creates_missing_profile(self, mock_run):
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")  # mode is provision-approved

        call_count = {"create": 0}

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_list(["default", "researcher", "analyst"]))
            elif "profile create" in cmd_str:
                call_count["create"] += 1
                return MagicMock(returncode=0, stdout="Created reviewer")
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        report = resolve_profiles(reg, existing=["default", "researcher", "analyst"], provision=True)
        assert call_count["create"] == 1  # Only reviewer was created
        assert report.summary["created"] == 1
        assert report.summary["reused"] == 2
        assert report.summary["all_ready"] is True


# ─── Test: Unknown Role ────────────────────────────────────────────

class TestUnknownRole:
    """Article test case: 'Unknown role name -> blocked'."""

    @patch("profile_check.subprocess.run")
    def test_unregistered_role_is_blocked(self, mock_run):
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_profile_list(["default"]))

        # Pass a role name not in the registry
        report = resolve_profiles(
            reg,
            existing=["default"],
            requested_roles=["researcher", "nonexistent-role"],
            provision=True,
        )
        unknown_result = [r for r in report.results if r.role == "nonexistent-role"][0]
        assert unknown_result.action == "blocked"
        assert "not in the approved registry" in unknown_result.reason


# ─── Test: Idempotency ─────────────────────────────────────────────

class TestIdempotency:
    """Article test case: 'Run twice -> second run does not create duplicates'."""

    @patch("profile_check.subprocess.run")
    def test_second_run_does_not_recreate(self, mock_run):
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")

        call_count = {"create": 0}

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                # All profiles exist already
                profiles = ["default", "researcher", "analyst", "reviewer"]
                return MagicMock(returncode=0, stdout=mock_profile_list(profiles))
            elif "profile create" in cmd_str:
                call_count["create"] += 1
                return MagicMock(returncode=0, stdout="Created")
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        report = resolve_profiles(reg, existing=["default", "researcher", "analyst", "reviewer"], provision=True)
        assert call_count["create"] == 0  # Nothing created — all existed
        assert report.summary["created"] == 0
        assert report.summary["reused"] == 3


# ─── Test: Phase 1 Boundary ────────────────────────────────────────

class TestPhaseOneBoundary:
    """execution_started must always be false; phase must always be profile-preparation."""

    @patch("profile_check.subprocess.run")
    def test_boundary_fields_enforced(self, mock_run):
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_profile_list(["default"]))

        report = resolve_profiles(reg, existing=["default"])
        d = report.to_dict()
        assert d["execution_started"] is False
        assert d["phase"] == "profile-preparation"


# ─── Test: Empty Registry ──────────────────────────────────────────

class TestEmptyRegistry:
    """Edge case: registry with zero roles should produce an empty but valid report."""

    @patch("profile_check.subprocess.run")
    def test_empty_registry_produces_valid_report(self, mock_run):
        from profile_check import resolve_profiles
        reg = load_fixture("empty-registry.yaml")
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_profile_list(["default"]))

        report = resolve_profiles(reg, existing=["default"])
        assert report.summary["total_roles"] == 0
        assert report.summary["all_ready"] is True  # vacuously true — no roles to block
        d = report.to_dict()
        assert d["execution_started"] is False


# ─── Test: Role Catalog (Task-Driven Mode) ────────────────────────

class TestRoleCatalog:
    """The role catalog is the bridge between a task description and role resolution."""

    def test_catalog_contains_all_roles(self):
        from profile_check import get_role_catalog
        reg = load_fixture("sample-registry.yaml")
        catalog = get_role_catalog(reg)
        role_names = [c["role"] for c in catalog]
        assert set(role_names) == {"researcher", "analyst", "reviewer"}

    def test_catalog_includes_capabilities(self):
        from profile_check import get_role_catalog
        reg = load_fixture("sample-registry.yaml")
        catalog = get_role_catalog(reg)
        for entry in catalog:
            assert "capabilities" in entry
            assert len(entry["capabilities"]) > 0  # every role has capability text

    def test_catalog_includes_skills_and_auto_create(self):
        from profile_check import get_role_catalog
        reg = load_fixture("sample-registry.yaml")
        catalog = get_role_catalog(reg)
        for entry in catalog:
            assert "skills" in entry
            assert "auto_create" in entry
            assert isinstance(entry["skills"], list)

    def test_empty_registry_catalog(self):
        from profile_check import get_role_catalog
        reg = load_fixture("empty-registry.yaml")
        catalog = get_role_catalog(reg)
        assert catalog == []


# ─── Test: --roles Flag (Agent Inference Output) ───────────────────

class TestRolesFlag:
    """After the agent infers roles from a task, it passes them via --roles."""

    @patch("profile_check.subprocess.run")
    def test_specific_roles_checked(self, mock_run):
        """Only the roles specified in requested_roles should appear in the report."""
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_profile_list(["default"]))

        # Agent inferred only researcher and reviewer from the task
        report = resolve_profiles(
            reg, existing=["default"],
            requested_roles=["researcher", "reviewer"],
        )
        roles_in_report = {r.role for r in report.results}
        assert roles_in_report == {"researcher", "reviewer"}
        assert "analyst" not in roles_in_report  # analyst was not requested

    @patch("profile_check.subprocess.run")
    def test_mixed_known_and_unknown_roles(self, mock_run):
        """One known role + one unknown role → known is checked, unknown is blocked."""
        from profile_check import resolve_profiles
        reg = load_fixture("sample-registry.yaml")

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_profile_list(["default"]))

        report = resolve_profiles(
            reg, existing=["default"],
            requested_roles=["researcher", "nonexistent-role"],
        )
        researcher = [r for r in report.results if r.role == "researcher"][0]
        unknown = [r for r in report.results if r.role == "nonexistent-role"][0]
        assert researcher.action == "blocked"  # missing, but recognized
        assert unknown.action == "blocked"     # not in registry at all
        assert "not in the approved registry" in unknown.reason


# ─── Test: Config Override Application (v3.0) ──────────────────────

class TestConfigOverrides:
    """Config overrides are applied after profile creation when --provision is used."""

    @patch("profile_check.subprocess.run")
    @patch("profile_check.apply_overrides_to_config")
    def test_overrides_applied_on_provision(self, mock_apply, mock_run):
        """When provisioning, config_overrides should be applied to the new profile."""
        from profile_check import resolve_profiles
        reg = load_fixture("registry-with-overrides.yaml")

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_list(["default"]))
            elif "profile create" in cmd_str:
                return MagicMock(returncode=0, stdout="Created")
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.home", return_value=Path("/tmp/fake-home")):
                report = resolve_profiles(reg, existing=["default"], provision=True)

        assert mock_apply.call_count >= 1

    @patch("profile_check.subprocess.run")
    def test_no_overrides_when_no_config_block(self, mock_run):
        """Roles without config_overrides should still provision successfully."""
        from profile_check import resolve_profiles
        reg = {
            "mode": "provision-approved",
            "max_auto_created_profiles": 4,
            "roles": {
                "simple-role": {
                    "description": "Simple",
                    "skills": [],
                    "auto_create": True,
                },
            },
        }

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_list(["default"]))
            elif "profile create" in cmd_str:
                return MagicMock(returncode=0, stdout="Created")
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        report = resolve_profiles(reg, existing=["default"], provision=True)
        assert report.summary["created"] == 1

    def test_model_never_in_fixture_overrides(self):
        """The registry fixture must not contain model in config_overrides."""
        reg = load_fixture("registry-with-overrides.yaml")
        for role_name, role_def in reg["roles"].items():
            overrides = role_def.get("config_overrides", {})
            assert "model" not in overrides, f"{role_name} has model in overrides — should be excluded"

    @patch("profile_check.subprocess.run")
    @patch("profile_check.apply_overrides_to_config")
    def test_no_config_flag_skips_overrides(self, mock_apply, mock_run):
        """When apply_config_overrides=False, overrides should NOT be applied."""
        from profile_check import resolve_profiles
        reg = load_fixture("registry-with-overrides.yaml")

        def mock_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "profile list" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_list(["default"]))
            elif "profile create" in cmd_str:
                return MagicMock(returncode=0, stdout="Created")
            elif "profile show" in cmd_str:
                return MagicMock(returncode=0, stdout=mock_profile_show(cmd[-1]))
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = mock_side_effect

        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.home", return_value=Path("/tmp/fake-home")):
                report = resolve_profiles(
                    reg, existing=["default"],
                    provision=True,
                    apply_config_overrides=False,
                )

        assert mock_apply.call_count == 0  # overrides skipped
