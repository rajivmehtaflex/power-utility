#!/usr/bin/env python3
"""Export an Unsloth adapter to adapter, merged 16-bit, or GGUF output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    from unsloth import FastLanguageModel
    from workflow_config import load_json, validate_config

    cfg = validate_config(load_json(args.config), "export")
    model_cfg = cfg["model"]
    export_cfg = cfg.get("export", {})
    source = cfg.get("training", {}).get("output_dir", "./outputs")
    target = Path(export_cfg.get("output", "./exported-model"))
    model, tokenizer = FastLanguageModel.from_pretrained(model_name=source, max_seq_length=cfg.get("training", {}).get("max_seq_length", 512), load_in_4bit=False)
    target.mkdir(parents=True, exist_ok=True)
    fmt = export_cfg.get("format", "adapter")
    if fmt == "adapter":
        model.save_pretrained(target)
        tokenizer.save_pretrained(target)
    elif fmt == "merged-16bit":
        model.save_pretrained_merged(target, tokenizer, save_method="merged_16bit")
    else:
        model.save_pretrained_gguf(target, tokenizer, quantization_method=export_cfg.get("quantization", "q4_k_m"))
    (target / "export_metadata.json").write_text(json.dumps({"source": source, "format": fmt, "model": model_cfg}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "format": fmt}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
