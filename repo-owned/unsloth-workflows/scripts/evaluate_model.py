#!/usr/bin/env python3
"""Evaluate baseline and adapter generations on held-out prompts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from workflow_config import load_json, validate_config

    cfg = validate_config(load_json(args.config), "evaluate")
    model_cfg = cfg["model"]
    eval_path = cfg["data"]["eval"]
    adapter = cfg.get("evaluation", {}).get("adapter") or cfg.get("training", {}).get("output_dir")
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["name"], revision=model_cfg.get("revision"))
    baseline_model = AutoModelForCausalLM.from_pretrained(model_cfg["name"], revision=model_cfg.get("revision"), device_map="auto")
    tuned_base = AutoModelForCausalLM.from_pretrained(model_cfg["name"], revision=model_cfg.get("revision"), device_map="auto") if adapter else baseline_model
    tuned = PeftModel.from_pretrained(tuned_base, adapter) if adapter else tuned_base
    samples = []
    for line in Path(eval_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        messages = row["messages"]
        inputs = tokenizer.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=True, return_tensors="pt").to(tuned.device)
        limit = cfg.get("evaluation", {}).get("max_new_tokens", 64)
        baseline_output = baseline_model.generate(inputs, max_new_tokens=limit)
        tuned_output = tuned.generate(inputs, max_new_tokens=limit)
        samples.append({
            "prompt": messages[-2]["content"],
            "baseline": tokenizer.decode(baseline_output[0][inputs.shape[-1]:], skip_special_tokens=True),
            "adapter": tokenizer.decode(tuned_output[0][inputs.shape[-1]:], skip_special_tokens=True),
        })
    target = Path(cfg.get("evaluation", {}).get("output", "evaluation.json"))
    target.write_text(json.dumps({"samples": samples, "count": len(samples)}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "count": len(samples)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
