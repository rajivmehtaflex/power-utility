# Edge AI Appliance Production Binding

Use this reference when documenting or deploying a compact local AI appliance such as NVIDIA DGX Spark.

## Evidence layers

Separate four layers instead of treating the appliance as a generic GPU server:

1. **Hardware contract:** record architecture (for example ARM64), unified-memory behavior, memory bandwidth, storage, network interfaces, power/thermal envelope, and whether an advertised model-size limit is a capacity claim rather than a throughput/SLA claim.
2. **OS baseline:** identify the vendor-supported OS, driver/firmware update path, recovery/reimaging posture, and OEM-versus-Founders-Edition differences. Prefer the vendor’s tested dashboard/update workflow for production and retain pre/post-update evidence.
3. **Serving route:** distinguish vLLM, llama.cpp, SGLang, TensorRT-LLM, and NIM by model format, architecture support, container architecture, API behavior, and multi-node support. Do not infer that an x86 CUDA container or model recipe transfers unchanged to ARM64.
4. **Application binding:** place an OpenAI-compatible model endpoint behind private networking, TLS, authentication, rate limits, health checks, observability, and restart/rollback. Keep the application pointed at a stable virtual route so the backend can move from one appliance to a small cluster or cloud fallback.

## Production checklist

- Verify `linux/arm64` image and dependency availability; x86-only wheels/binaries are a compatibility gate.
- Validate Docker plus NVIDIA Container Toolkit before debugging the model server.
- Use NGC authentication and pinned image/model versions; never put registry credentials in images or source.
- Distinguish hosted APIs from local serving: a provider’s hosted OpenAI-compatible URL does not prove inference is running on the local appliance.
- Verify NIM licensing/support and model-specific device profiles; not every NIM is available or supported on every appliance.
- Load-test shared-memory bandwidth, KV-cache/concurrency limits, and failure recovery rather than relying on parameter-count marketing.
- Treat multi-node networking and orchestration as a separate compatibility gate; verify the exact engine’s sharding/Ray/NCCL/RDMA path before recommending a cluster.

## Route matrix

| Route | Best fit | Verify before production |
|---|---|---|
| vLLM | Multi-user throughput and batching | ARM64 image, exact model recipe, context/KV-cache settings, tool calls, multi-node path |
| llama.cpp | GGUF breadth and lightweight private serving | CUDA build, GGUF compatibility, memory fit, `llama-server` API behavior |
| NIM | NVIDIA-supported microservice path | Spark-compatible profile/image, NGC access, entitlement and commercial-use terms |
| Custom service | Specialized workload | GPU/container access, API contract, lifecycle, observability, rollback |

## Recommended topology

```text
Applications -> API gateway (TLS/auth/rate limits) -> private model endpoint
                                                   -> vLLM/llama.cpp/NIM
                                                   -> persistent model volume
                                                   -> metrics/logs
```

Keep the application pointed at a stable virtual route such as `https://dgx-spark.internal.example.com/v1`; this enables later migration to a second appliance, a small cluster, or a cloud fallback without changing application code.
