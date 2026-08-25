#!/usr/bin/env python3
"""
Config Merger for Profile Overrides
====================================

Deep-merges a config_overrides dict into a base config.yaml dict.
Used by profile_check.py after `hermes profile create` to apply
role-specific configuration to a freshly created profile.

Rules:
  - Top-level keys are merged individually (agent, memory, toolsets, etc.)
  - Within each section, individual fields are overridden (not whole section)
  - Lists (like toolsets) are REPLACED, not merged
  - The 'model' top-level key is NEVER touched
  - The 'providers' top-level key is NEVER touched
"""

from __future__ import annotations

from typing import Any, Dict

# Keys that must never be modified by config overrides
PROTECTED_KEYS = frozenset({
    "model",
    "providers",
    "mcp_servers",
    "platform_toolsets",
    "fallback_providers",
    "fallback_model",
})


def deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-merge overrides into base config dict.

    - Nested dicts are merged recursively (field-by-field).
    - Lists are replaced entirely (the override defines the exact list).
    - Scalar values are overwritten.
    - Protected keys (model, providers, etc.) are skipped even if present in overrides.

    Returns a NEW dict; does not mutate inputs.
    """
    result = dict(base)  # shallow copy of top-level

    for key, override_value in overrides.items():
        # Skip protected keys entirely
        if key in PROTECTED_KEYS:
            continue

        # If the override value is a dict AND the base value is a dict, merge recursively
        if isinstance(override_value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], override_value)
        else:
            # Lists, scalars, and type mismatches: replace entirely
            result[key] = override_value

    return result


def apply_overrides_to_config(
    config_path: str,
    overrides: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Read a config.yaml, apply overrides, write back, return the new config.

    Args:
        config_path: Path to the profile's config.yaml.
        overrides:   The config_overrides dict from the registry.

    Returns:
        The merged config dict (also written to disk).
    """
    import yaml
    from pathlib import Path

    p = Path(config_path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(p) as f:
        base_config = yaml.safe_load(f) or {}

    merged = deep_merge(base_config, overrides)

    with open(p, "w") as f:
        yaml.dump(merged, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return merged


def validate_overrides(overrides: Dict[str, Any]) -> list:
    """
    Check for protected keys in overrides and return warnings.

    Returns a list of warning strings (empty if clean).
    """
    warnings = []
    for key in overrides:
        if key in PROTECTED_KEYS:
            warnings.append(
                f"'{key}' is a protected key and will be skipped. "
                f"Set it manually via the Hermes CLI."
            )
    return warnings
