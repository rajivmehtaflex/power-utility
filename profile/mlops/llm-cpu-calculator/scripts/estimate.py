#!/usr/bin/env python3
"""LLM CPU/RAM requirement estimator for a NAMED TARGET machine.

Implements the calculation rules in SKILL.md. Stdlib only; no network,
no model download. The machine executing this script is only the
calculator host -- the numbers describe the target machine named by the
user, never this host.

Examples:
  # 9B target, measured Q4_K_M file (5.9 GB), 8 KV layers, 4k ctx, 1 seq
  python3 estimate.py --params 9 --weight-file 5.9 \
      --layers 8 --kv-heads 4 --head-dim 256 --ctx 4096

  # same, from effective bits, + 340M drafter (speculative decoding),
  # verdict against a 16 GiB target
  python3 estimate.py --params 9 --bits 4.8 --layers 8 --kv-heads 4 \
      --head-dim 256 --ctx 4096 --draft-params 0.34 --draft-bits 16 \
      --target-ram 16
"""

import argparse
import json
import math
import sys

GIB = 2 ** 30


def params_to_gib(params_b: float, bits: float) -> float:
    """Rule 1: parameters (billions) x effective bits/param -> GiB."""
    return params_b * 1e9 * (bits / 8) / GIB


def file_to_gib(size_gb: float) -> float:
    """Measured file size in GB (10^9 bytes) -> GiB."""
    return size_gb * 1e9 / GIB


def kv_to_gib(layers: int, ctx: int, seq: int, kv_heads: int,
              head_dim: int, bytes_per_val: int) -> float:
    """Rule 2: 2 (K+V) x layers x ctx x seq x kv_heads x head_dim x bytes."""
    kv_bytes = 2 * layers * ctx * seq * kv_heads * head_dim * bytes_per_val
    return kv_bytes / GIB


def cpu_tier(params_b: float):
    """Heuristic physical-core tiers (minimum, recommended). Not a throughput guarantee."""
    if params_b < 7:
        return "4", "6-8"
    if params_b < 20:
        return "8", "8-12"
    if params_b < 40:
        return "12-16", "12-16"
    return "16+", "24+"


def verdict(total: float, target_ram):
    """Suitability verdict for the named target only. None = no specs supplied."""
    if target_ram is None:
        return None
    if total <= 0.85 * target_ram:
        return "pass (>=15% headroom on the stated target RAM)"
    if total <= target_ram:
        return ("constrained -- fits only by eating into the safety margin; "
                "swap-backed execution must be flagged, not treated as feasible")
    return "unsuitable -- working set exceeds the stated target RAM (swap thrashing risk)"


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--params", type=float, required=True,
                   help="target parameter count in billions (e.g. 9)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--bits", type=float,
                     help="effective bits per parameter (e.g. 4.8 for Q4_K_M)")
    src.add_argument("--weight-file", type=float,
                     help="measured target model file size in GB (preferred)")
    p.add_argument("--draft-params", type=float, default=0.0,
                   help="draft parameter count in billions (0 = no spec decoding)")
    p.add_argument("--draft-bits", type=float, default=16.0)
    p.add_argument("--draft-weight-file", type=float,
                   help="measured draft file size in GB")
    p.add_argument("--layers", type=int,
                   help="KV-bearing (attention) layers of the target")
    p.add_argument("--kv-heads", type=int)
    p.add_argument("--head-dim", type=int)
    p.add_argument("--kv-bytes", type=int, default=2, choices=(1, 2),
                   help="bytes per KV value: 2=FP16/BF16, 1=8-bit KV")
    p.add_argument("--draft-layers", type=int,
                   help="draft KV-bearing layers (draft KV computed only if set)")
    p.add_argument("--ctx", type=int, default=4096,
                   help="context tokens (default 4096 -- stated assumption)")
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--overhead-pct", type=float, default=15.0,
                   help="runtime overhead as %% of weights (default 15)")
    p.add_argument("--os-reserve", type=float, default=6.0,
                   help="OS/runtime reserve on the target in GiB (default 6)")
    p.add_argument("--margin-pct", type=float, default=25.0,
                   help="safety margin %% added to working set (default 25)")
    p.add_argument("--target-ram", type=float,
                   help="installed RAM of the NAMED target in GiB (enables verdict)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args()

    warnings = []
    if args.weight_file is not None:
        t_weights = file_to_gib(args.weight_file)
        t_src = f"measured file {args.weight_file:g} GB"
    else:
        t_weights = params_to_gib(args.params, args.bits)
        t_src = f"{args.params:g}B @ {args.bits:g} bits"

    d_weights = 0.0
    d_src = None
    if args.draft_weight_file is not None:
        d_weights = file_to_gib(args.draft_weight_file)
        d_src = f"measured file {args.draft_weight_file:g} GB"
    elif args.draft_params > 0:
        d_weights = params_to_gib(args.draft_params, args.draft_bits)
        d_src = f"{args.draft_params:g}B @ {args.draft_bits:g} bits"

    spec = args.layers is not None and args.kv_heads and args.head_dim
    t_kv = (kv_to_gib(args.layers, args.ctx, args.concurrency,
                      args.kv_heads, args.head_dim, args.kv_bytes)
            if spec else None)
    if not spec:
        warnings.append("KV geometry not supplied (--layers/--kv-heads/--head-dim): "
                        "KV cache omitted from the total -- add it or treat the "
                        "result as weights-only.")
    d_kv = (kv_to_gib(args.draft_layers, args.ctx, args.concurrency,
                      args.kv_heads, args.head_dim, args.kv_bytes)
            if (args.draft_layers and spec) else 0.0)

    overhead = (t_weights + d_weights) * args.overhead_pct / 100.0
    total = t_weights + d_weights + (t_kv or 0.0) + d_kv + overhead + args.os_reserve
    recommended = math.ceil(total * (1 + args.margin_pct / 100.0))
    t_min, t_rec = cpu_tier(args.params)
    v = verdict(total, args.target_ram)

    if args.json:
        print(json.dumps({
            "target_machine_only": True,
            "weights": {"target_gib": round(t_weights, 3), "source": t_src,
                        "draft_gib": round(d_weights, 3), "draft_source": d_src},
            "kv_cache_gib": {"target": round(t_kv, 4) if t_kv is not None else None,
                             "draft": round(d_kv, 4),
                             "ctx_tokens": args.ctx, "concurrency": args.concurrency},
            "runtime_overhead_gib": round(overhead, 3),
            "os_reserve_gib": args.os_reserve,
            "total_working_set_gib": round(total, 3),
            "recommended_installed_gib_min": recommended,
            "margin_pct": args.margin_pct,
            "cpu_tier": {"minimum_cores": t_min, "recommended_cores": t_rec},
            "verdict_for_named_target": v,
            "warnings": warnings,
        }, indent=2))
        return 0

    kv_note = (f"{args.layers}L x {args.kv_heads}H x {args.head_dim}D, "
               f"{'fp16' if args.kv_bytes == 2 else 'q8'} KV")
    lines = [
        "LLM CPU/RAM estimate -- describes the NAMED TARGET machine only",
        "(the host running this script is just the calculator)",
        "",
        f"{'Component':<44}{'GiB':>8}",
        "-" * 52,
        f"{'Target weights (' + t_src + ')':<44}{t_weights:>8.2f}",
    ]
    if d_src:
        lines.append(f"{'Draft weights (' + d_src + ')':<44}{d_weights:>8.2f}")
    if t_kv is not None:
        lines.append(f"{'Target KV (' + kv_note + ')':<44}{t_kv:>8.3f}")
        lines.append(f"{'  @ ' + f'{args.ctx:,}' + ' tok x ' + str(args.concurrency) + ' seq':<44}{'':>8}")
    if d_kv:
        lines.append(f"{'Draft KV':<44}{d_kv:>8.3f}")
    lines += [
        f"{'Runtime overhead (' + f'{args.overhead_pct:g}' + '% of weights)':<44}{overhead:>8.2f}",
        f"{'OS / system reserve (on target)':<44}{args.os_reserve:>8.2f}",
        "-" * 52,
        f"{'TOTAL working set':<44}{total:>8.2f}",
        f"{'Recommended installed (+' + f'{args.margin_pct:g}' + '% margin)':<44}{'>= ' + str(recommended):>8}",
        "",
        f"CPU tier (heuristic, target): minimum {t_min} physical cores, recommended {t_rec}",
        "SIMD on target: AVX2/AVX-512 (x86) or NEON/ASIMD (ARM) preferred",
        "Threads on Linux target: start at physical cores - 1..2, then benchmark",
    ]
    if v:
        lines.append(f"Verdict for named target ({args.target_ram:g} GiB): {v}")
    else:
        lines.append("Verdict: requirements only -- no target RAM supplied, no verdict possible")
    for w in warnings:
        lines.append(f"WARNING: {w}")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
