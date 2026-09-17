#!/usr/bin/env python3
"""Execute the built-in Unsloth text SFT workflow inside the managed venv."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from data_validation import messages_from_record


def _load_rows(path: str):
    from datasets import Dataset

    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append({"messages": messages_from_record(row)})
    return Dataset.from_list(rows)


def _file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    from unsloth import FastLanguageModel
    from trl import SFTConfig, SFTTrainer
    from workflow_config import load_json, validate_config

    cfg = validate_config(load_json(args.config), "train")
    model_cfg = cfg["model"]
    train_cfg = cfg.get("training", {})
    data_cfg = cfg["data"]
    method = train_cfg.get("method", "qlora")
    max_length = train_cfg.get("max_seq_length", 512)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_cfg["name"],
        revision=model_cfg.get("revision"),
        max_seq_length=max_length,
        load_in_4bit=method == "qlora",
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=train_cfg.get("lora_r", 16),
        lora_alpha=train_cfg.get("lora_alpha", 16),
        lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
    )
    dataset = _load_rows(data_cfg["train"])
    eval_dataset = _load_rows(data_cfg["eval"]) if data_cfg.get("eval") else None

    def format_rows(batch):
        return {"text": [tokenizer.apply_chat_template(x, tokenize=False, add_generation_prompt=False) for x in batch["messages"]]}

    dataset = dataset.map(format_rows, batched=True)
    eval_interval = max(1, train_cfg.get("eval_steps", train_cfg.get("save_steps", 10)))
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        args=SFTConfig(
            output_dir=train_cfg.get("output_dir", "./outputs"),
            max_seq_length=max_length,
            per_device_train_batch_size=train_cfg.get("batch_size", 1),
            gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 1),
            learning_rate=train_cfg.get("learning_rate", 2e-4),
            max_steps=train_cfg.get("max_steps", 10),
            num_train_epochs=train_cfg.get("num_epochs", 1),
            logging_steps=1,
            save_steps=train_cfg.get("save_steps", 10),
            eval_strategy="steps" if eval_dataset is not None else "no",
            eval_steps=eval_interval,
            report_to="none",
        ),
    )
    trainer.train(resume_from_checkpoint=train_cfg.get("resume_from_checkpoint"))
    output = Path(train_cfg.get("output_dir", "./outputs"))
    model.save_pretrained(output)
    tokenizer.save_pretrained(output)
    metadata = {
        "model": model_cfg,
        "training": train_cfg,
        "datasets": {"train": {"path": data_cfg["train"], "sha256": _file_sha256(data_cfg["train"])}},
        "tokenizer": {"name_or_path": tokenizer.name_or_path, "chat_template": tokenizer.chat_template},
        "dependencies": {
            package: importlib.metadata.version(package)
            for package in ("unsloth", "torch", "transformers", "trl", "peft", "datasets")
        },
    }
    if data_cfg.get("eval"):
        metadata["datasets"]["eval"] = {"path": data_cfg["eval"], "sha256": _file_sha256(data_cfg["eval"])}
    (output / "training_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
