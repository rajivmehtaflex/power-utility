#!/usr/bin/env python3
"""Portable command runner for common Unsloth workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from data_validation import validate_dataset
from environment import doctor, setup
from workflow_config import ConfigError, load_json, validate_config


def _emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _project(args: argparse.Namespace) -> Path:
    return Path(args.project or ".").expanduser().resolve()


def _load_and_validate(args: argparse.Namespace) -> dict:
    if not args.config:
        raise ConfigError(f"--config is required for {args.command}")
    return validate_config(load_json(args.config), args.command)


def _run_python(project: Path, script: str, config: str) -> int:
    python = project / ".unsloth" / "venv" / "bin" / "python"
    runner = Path(__file__).resolve().parent / script
    return subprocess.run([str(python), str(runner), "--config", str(Path(config).resolve())], cwd=project, check=False).returncode


def _project_path(project: Path, value: str) -> str:
    candidate = Path(value).expanduser()
    return str(candidate if candidate.is_absolute() else project / candidate)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Linux/NVIDIA Unsloth workflow runner")
    parser.add_argument("command", choices=["doctor", "setup", "validate-data", "train", "evaluate", "export"])
    parser.add_argument("--project", default=".")
    parser.add_argument("--config")
    parser.add_argument("--dataset")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        project = _project(args)
        if args.command == "doctor":
            _emit(doctor(project))
            return 0
        if args.command == "setup":
            _emit(setup(project, args.dry_run))
            return 0
        if args.command == "validate-data":
            dataset = args.dataset
            if not dataset and args.config:
                cfg = validate_config(load_json(args.config), "validate-data")
                dataset = cfg.get("data", {}).get("train")
            if not dataset:
                raise ConfigError("provide --dataset or data.train in --config")
            report = validate_dataset(dataset)
            _emit(report)
            return 0 if not report["errors"] else 1
        cfg = _load_and_validate(args)
        if args.dry_run:
            _emit({"command": args.command, "dry_run": True, "project": str(project), "config": cfg})
            return 0
        setup(project, False)
        if args.command == "train":
            cfg["data"]["train"] = _project_path(project, cfg["data"]["train"])
            if cfg["data"].get("eval"):
                cfg["data"]["eval"] = _project_path(project, cfg["data"]["eval"])
            report = validate_dataset(cfg["data"]["train"])
            if report["errors"]:
                _emit(report)
                return 1
            if cfg["data"].get("eval"):
                eval_report = validate_dataset(cfg["data"]["eval"])
                if eval_report["errors"]:
                    _emit(eval_report)
                    return 1
            return _run_python(project, "sft_train.py", args.config)
        if args.command == "evaluate":
            return _run_python(project, "evaluate_model.py", args.config)
        return _run_python(project, "export_model.py", args.config)
    except (ConfigError, RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
