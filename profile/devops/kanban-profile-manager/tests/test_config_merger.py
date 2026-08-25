# tests/test_config_merger.py
"""Tests for the config merger utility."""
import os
import sys
import copy
from pathlib import Path

import pytest
import yaml

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPT_DIR)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return yaml.safe_load(f)


class TestDeepMerge:
    def test_scalar_override(self):
        from config_merger import deep_merge
        base = {"agent": {"max_turns": 90, "verbose": False}}
        overrides = {"agent": {"max_turns": 20}}
        result = deep_merge(base, overrides)
        assert result["agent"]["max_turns"] == 20
        assert result["agent"]["verbose"] is False  # unchanged

    def test_nested_dict_merge(self):
        from config_merger import deep_merge
        base = {"agent": {"max_turns": 90, "reasoning_effort": "medium"}}
        overrides = {"agent": {"reasoning_effort": "high"}}
        result = deep_merge(base, overrides)
        assert result["agent"]["max_turns"] == 90   # kept
        assert result["agent"]["reasoning_effort"] == "high"  # overridden

    def test_list_replaced_not_merged(self):
        from config_merger import deep_merge
        base = {"toolsets": ["hermes-cli", "hermes-telegram"]}
        overrides = {"toolsets": ["hermes-cli"]}
        result = deep_merge(base, overrides)
        assert result["toolsets"] == ["hermes-cli"]  # replaced, not concatenated

    def test_model_key_never_touched(self):
        from config_merger import deep_merge
        base = {"model": {"default": "gpt-4", "provider": "openai"}}
        overrides = {"model": {"default": "claude-3"}}
        result = deep_merge(base, overrides)
        assert result["model"]["default"] == "gpt-4"  # unchanged!

    def test_providers_key_never_touched(self):
        from config_merger import deep_merge
        base = {"providers": {"openrouter": {"api_key": "sk-xxx"}}}
        overrides = {"providers": {"openrouter": {"api_key": "sk-yyy"}}}
        result = deep_merge(base, overrides)
        assert result["providers"]["openrouter"]["api_key"] == "sk-xxx"  # unchanged!

    def test_new_key_added(self):
        from config_merger import deep_merge
        base = {"agent": {"max_turns": 90}}
        overrides = {"display": {"personality": "technical"}}
        result = deep_merge(base, overrides)
        assert result["display"]["personality"] == "technical"
        assert result["agent"]["max_turns"] == 90

    def test_does_not_mutate_inputs(self):
        from config_merger import deep_merge
        base = {"agent": {"max_turns": 90}}
        base_copy = copy.deepcopy(base)
        overrides = {"agent": {"max_turns": 20}}
        deep_merge(base, overrides)
        assert base == base_copy  # base not mutated


class TestValidateOverrides:
    def test_warns_on_model_key(self):
        from config_merger import validate_overrides
        warnings = validate_overrides({"model": {"default": "x"}, "agent": {"max_turns": 20}})
        assert len(warnings) == 1
        assert "model" in warnings[0]

    def test_no_warnings_for_safe_keys(self):
        from config_merger import validate_overrides
        warnings = validate_overrides({"agent": {"max_turns": 20}, "memory": {"memory_enabled": False}})
        assert warnings == []

    def test_warns_on_all_protected_keys(self):
        from config_merger import validate_overrides
        warnings = validate_overrides({
            "model": {}, "providers": {}, "mcp_servers": {},
            "platform_toolsets": {},
        })
        assert len(warnings) == 4


class TestApplyOverridesToConfig:
    def test_writes_merged_config(self, tmp_path):
        from config_merger import apply_overrides_to_config
        # Copy base config to temp
        base = load_fixture("base-config.yaml")
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(base, f)

        overrides = {"agent": {"max_turns": 20}, "memory": {"memory_enabled": False}}
        result = apply_overrides_to_config(str(config_path), overrides)

        # Verify returned dict
        assert result["agent"]["max_turns"] == 20
        assert result["memory"]["memory_enabled"] is False
        # Verify file was written
        with open(config_path) as f:
            written = yaml.safe_load(f)
        assert written["agent"]["max_turns"] == 20
        assert written["memory"]["memory_enabled"] is False

    def test_model_preserved_after_apply(self, tmp_path):
        from config_merger import apply_overrides_to_config
        base = load_fixture("base-config.yaml")
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(base, f)

        # Try to override model — should be ignored
        overrides = {"model": {"default": "new-model"}}
        result = apply_overrides_to_config(str(config_path), overrides)
        assert result["model"]["default"] == "test-model"  # unchanged

    def test_raises_on_missing_file(self, tmp_path):
        from config_merger import apply_overrides_to_config
        with pytest.raises(FileNotFoundError):
            apply_overrides_to_config(str(tmp_path / "nonexistent.yaml"), {})
