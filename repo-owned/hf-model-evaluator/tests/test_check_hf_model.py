"""Unit tests for hf-model-evaluator check_hf_model script."""

import os
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_hf_model


class TestHFModelEvaluator(unittest.TestCase):

    def test_parse_hf_target(self):
        # Direct repo ID
        target_type, ident = check_hf_model.parse_hf_target("Qwen/Qwen2.5-Coder-32B")
        self.assertEqual(target_type, "model")
        self.assertEqual(ident, "Qwen/Qwen2.5-Coder-32B")

        # Full URL
        target_type, ident = check_hf_model.parse_hf_target("https://huggingface.co/deepseek-ai/DeepSeek-V3")
        self.assertEqual(target_type, "model")
        self.assertEqual(ident, "deepseek-ai/DeepSeek-V3")

        # Short URL (hf.co)
        target_type, ident = check_hf_model.parse_hf_target("https://hf.co/meta-llama/Llama-3.2-1B")
        self.assertEqual(target_type, "model")
        self.assertEqual(ident, "meta-llama/Llama-3.2-1B")

        # Collection URL
        target_type, ident = check_hf_model.parse_hf_target("https://huggingface.co/collections/LiquidAI/lfm3-6adc03dcfe62bfd2fcd8eea7")
        self.assertEqual(target_type, "collection")
        self.assertEqual(ident, "LiquidAI/lfm3-6adc03dcfe62bfd2fcd8eea7")

    def test_assess_model_fit_pass(self):
        model_info = {
            "repo_id": "test/small-model",
            "model_type": "llama",
            "architectures": ["LlamaForCausalLM"],
            "is_moe": False,
            "total_download_gb": 4.0,
            "gguf_files": [],
            "gated": False,
        }
        hw_profile = {
            "ram_total_gb": 32.0,
            "disk_free_gb": 100.0,
            "gpus": [{"vram_total_bytes": 16 * 1_000_000_000}],
            "hf_cli": {"installed": True},
        }
        assessment = check_hf_model.assess_model_fit(model_info, hw_profile)
        self.assertEqual(assessment["status"], "PASS")
        self.assertTrue(assessment["fits"])
        self.assertEqual(assessment["download_size_gb"], 4.0)

    def test_assess_model_fit_needs_ram(self):
        model_info = {
            "repo_id": "test/huge-model",
            "model_type": "llama",
            "architectures": ["LlamaForCausalLM"],
            "is_moe": False,
            "total_download_gb": 70.0,
            "gguf_files": [],
            "gated": False,
        }
        hw_profile = {
            "ram_total_gb": 16.0,
            "disk_free_gb": 200.0,
            "gpus": [],
            "hf_cli": {},
        }
        assessment = check_hf_model.assess_model_fit(model_info, hw_profile)
        self.assertEqual(assessment["status"], "NEEDS_RAM")
        self.assertFalse(assessment["fits"])

    def test_assess_model_fit_needs_disk(self):
        model_info = {
            "repo_id": "test/medium-model",
            "model_type": "llama",
            "architectures": ["LlamaForCausalLM"],
            "is_moe": False,
            "total_download_gb": 30.0,
            "gguf_files": [],
            "gated": False,
        }
        hw_profile = {
            "ram_total_gb": 64.0,
            "disk_free_gb": 10.0,
            "gpus": [],
            "hf_cli": {},
        }
        assessment = check_hf_model.assess_model_fit(model_info, hw_profile)
        self.assertEqual(assessment["status"], "NEEDS_DISK")
        self.assertFalse(assessment["fits"])

    def test_colibri_moe_streaming_fit(self):
        model_info = {
            "repo_id": "puwaer/DeepSeek-V4-Flash-0731-reap-150b",
            "model_type": "deepseek_v4",
            "architectures": ["DeepseekV4ForCausalLM"],
            "is_moe": True,
            "total_download_gb": 85.0,
            "gguf_files": [],
            "gated": False,
        }
        hw_profile = {
            "ram_total_gb": 56.0,
            "disk_free_gb": 120.0,
            "gpus": [],
            "hf_cli": {"installed": True},
        }
        assessment = check_hf_model.assess_model_fit(model_info, hw_profile)
        self.assertEqual(assessment["status"], "PASS")
        self.assertTrue(assessment["fits"])
        self.assertEqual(assessment["colibri_family"], "deepseek_v4")
        self.assertIn("streams experts from SSD", assessment["execution_mode"])

    def test_gguf_quant_selection(self):
        model_info = {
            "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
            "model_type": "qwen2",
            "architectures": ["Qwen2ForCausalLM"],
            "is_moe": False,
            "total_download_gb": 80.0,
            "gguf_files": [
                {"path": "qwen2.5-coder-7b-instruct-q4_0-00001-of-00002.gguf", "size_gb": 3.98},
                {"path": "qwen2.5-coder-7b-instruct-q4_0-00002-of-00002.gguf", "size_gb": 0.45},
                {"path": "qwen2.5-coder-7b-instruct-q4_k_m.gguf", "size_gb": 4.68},
                {"path": "qwen2.5-coder-7b-instruct-q8_0.gguf", "size_gb": 8.10},
            ],
            "gated": False,
        }
        hw_profile = {
            "ram_total_gb": 32.0,
            "disk_free_gb": 50.0,
            "gpus": [],
            "hf_cli": {"installed": True},
        }
        assessment = check_hf_model.assess_model_fit(model_info, hw_profile)
        self.assertEqual(assessment["status"], "PASS")
        # Should select the standalone Q4_K_M
        self.assertEqual(assessment["selected_gguf"]["path"], "qwen2.5-coder-7b-instruct-q4_k_m.gguf")
        self.assertEqual(assessment["download_size_gb"], 4.68)


if __name__ == "__main__":
    unittest.main()
