#!/usr/bin/env python3
"""Evaluate baseline and adapter generations on held-out prompts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from data_validation import messages_from_record


def _full_sequence_loss(model, tokenizer, messages):
    import torch

    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        return model(**inputs, labels=inputs.input_ids).loss.item()


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
    samples = []
    rows = []
    for line in Path(eval_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(messages_from_record(json.loads(line)))
    baseline_model = AutoModelForCausalLM.from_pretrained(model_cfg["name"], revision=model_cfg.get("revision"), device_map="auto")
    limit = cfg.get("evaluation", {}).get("max_new_tokens", 64)
    baseline = []
    baseline_losses = []
    for messages in rows:
        inputs = tokenizer.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=True, return_tensors="pt").to(baseline_model.device)
        output = baseline_model.generate(inputs, max_new_tokens=limit)
        baseline.append(tokenizer.decode(output[0][inputs.shape[-1]:], skip_special_tokens=True))
        baseline_losses.append(_full_sequence_loss(baseline_model, tokenizer, messages))
    if adapter:
        del baseline_model
        import torch
        torch.cuda.empty_cache()
        tuned_base = AutoModelForCausalLM.from_pretrained(model_cfg["name"], revision=model_cfg.get("revision"), device_map="auto")
        tuned = PeftModel.from_pretrained(tuned_base, adapter)
    else:
        tuned = None
    exact_matches = 0
    adapter_losses = []
    for messages, baseline_text in zip(rows, baseline):
        active = tuned or baseline_model
        inputs = tokenizer.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=True, return_tensors="pt").to(active.device)
        tuned_output = active.generate(inputs, max_new_tokens=limit)
        adapter_text = tokenizer.decode(tuned_output[0][inputs.shape[-1]:], skip_special_tokens=True)
        adapter_losses.append(_full_sequence_loss(active, tokenizer, messages))
        expected = messages[-1]["content"]
        exact_matches += adapter_text.strip() == expected.strip()
        samples.append({
            "prompt": messages[-2]["content"],
            "expected": expected,
            "baseline": baseline_text,
            "adapter": adapter_text,
        })
    target = Path(cfg.get("evaluation", {}).get("output", "evaluation.json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "samples": samples,
        "count": len(samples),
        "exact_match": exact_matches / len(samples) if samples else None,
        "loss": {
            "baseline_full_sequence": sum(baseline_losses) / len(baseline_losses) if baseline_losses else None,
            "adapter_full_sequence": sum(adapter_losses) / len(adapter_losses) if adapter_losses else None,
        },
    }
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "count": len(samples), "exact_match": report["exact_match"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
