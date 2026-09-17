# Framework map

Unsloth is an optimization and workflow layer around PyTorch, Transformers, Hugging Face Datasets, PEFT, and TRL. The lifecycle is:

**model + tokenizer → dataset + chat template → learning objective → parameter method → optimized training → evaluation → export → inference**

Learning objective and parameter method are independent. SFT/CPT/DPO/GRPO describe the learning signal; FFT/LoRA/QLoRA describe which weights and precision are used.

Use CPT for raw domain/language text, SFT for demonstrations, preference methods for ranked responses, and RL when a reward function or environment can score generated attempts. Begin with a small instruct model and QLoRA unless a concrete reason requires another choice.

Source: [fine-tuning guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide.md), [datasets guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide.md).
