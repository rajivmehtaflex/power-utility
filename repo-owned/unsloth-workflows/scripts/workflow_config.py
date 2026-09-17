"""Strict, dependency-free configuration validation for Unsloth workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


SECTION_KEYS = {
    "model": {"name", "revision"},
    "data": {"train", "eval", "format"},
    "training": {
        "method", "output_dir", "max_steps", "num_epochs", "batch_size",
        "gradient_accumulation_steps", "learning_rate", "max_seq_length",
        "save_steps", "eval_steps", "lora_r", "lora_alpha", "resume_from_checkpoint",
    },
    "evaluation": {"adapter", "output", "max_new_tokens"},
    "export": {"format", "output", "quantization", "verify"},
}


def load_json(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {source}: {exc.msg} at line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise ConfigError("config root must be a JSON object")
    return value


def validate_config(value: dict[str, Any], command: str) -> dict[str, Any]:
    allowed = set(SECTION_KEYS)
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigError(f"unknown config key(s): {', '.join(unknown)}")
    for section, allowed_keys in SECTION_KEYS.items():
        section_value = value.get(section)
        if section_value is None:
            continue
        if not isinstance(section_value, dict):
            raise ConfigError(f"{section} must be an object")
        nested_unknown = sorted(set(section_value) - allowed_keys)
        if nested_unknown:
            names = ", ".join(f"{section}.{key}" for key in nested_unknown)
            raise ConfigError(f"unknown config key(s): {names}")
    if command in {"train", "evaluate", "export"} and not isinstance(value.get("model"), dict):
        raise ConfigError("model must be an object with a name")
    model = value.get("model", {})
    if model and (not isinstance(model.get("name"), str) or not model["name"].strip()):
        raise ConfigError("model.name must be a non-empty string")
    if command == "train":
        data = value.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("train"), str) or not data["train"].strip():
            raise ConfigError("data.train must be a non-empty path for training")
        training = value.get("training", {})
        if not isinstance(training, dict):
            raise ConfigError("training must be an object")
        method = training.get("method", "qlora")
        if method not in {"lora", "qlora"}:
            raise ConfigError("training.method must be 'lora' or 'qlora'")
        for key in ("max_steps", "max_seq_length", "batch_size", "gradient_accumulation_steps"):
            if key in training and (not isinstance(training[key], int) or training[key] < 1):
                raise ConfigError(f"training.{key} must be a positive integer")
        for key in ("num_epochs", "learning_rate", "lora_r", "lora_alpha", "save_steps", "eval_steps"):
            if key in training and (not isinstance(training[key], (int, float)) or isinstance(training[key], bool) or training[key] < 0):
                raise ConfigError(f"training.{key} must be a non-negative number")
    if command == "export":
        export = value.get("export", {})
        if not isinstance(export, dict):
            raise ConfigError("export must be an object")
        if export.get("format", "adapter") not in {"adapter", "merged-16bit", "gguf"}:
            raise ConfigError("export.format must be adapter, merged-16bit, or gguf")
    if command == "evaluate":
        data = value.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("eval"), str) or not data["eval"].strip():
            raise ConfigError("data.eval must be a non-empty path for evaluation")
        evaluation = value.get("evaluation", {})
        if "max_new_tokens" in evaluation and (not isinstance(evaluation["max_new_tokens"], int) or evaluation["max_new_tokens"] < 1):
            raise ConfigError("evaluation.max_new_tokens must be a positive integer")
    return value
