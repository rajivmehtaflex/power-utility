# Colab `exec` vs `ssh` GPU Visibility

Reproduction from 2026-08-23 session `g-gemma-4-12b` (T4 15360 MiB).

## The Difference

- `colab exec` → **kernel container** (`/usr/local/bin/jupyter-server`, `/usr/bin/python3 -m colab_kernel_launcher`) where `/usr/local/cuda` and `libnvidia-ml.so` are mounted. CUDA works.
- `ssh g-xxx` → **host VM** (`/sbin/docker-init`, `sshd: /usr/sbin/sshd`) root FS. CUDA driver not in PATH. `nvidia-smi` fails.

## Reproduction

```bash
export PYTHONPATH=""
colab --auth=adc new -s g-gemma-4-12b --gpu T4

# Via exec (works)
cat > /tmp/check.py << 'PY'
import torch, subprocess
print(torch.cuda.is_available())  # True
print(torch.cuda.get_device_name(0))  # Tesla T4
print(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout[:500])
PY
colab --auth=adc exec -s g-gemma-4-12b -f /tmp/check.py
# → cuda True, Tesla T4 15360 MiB

# Via ssh (fails)
ssh g-gemma-4-12b "python3 -c 'import torch; print(torch.cuda.is_available())'"
# → False
ssh g-gemma-4-12b "nvidia-smi 2>&1 | head"
# → NVIDIA-SMI couldn't find libnvidia-ml.so library

# Direct host ps shows the separation:
ssh g-gemma-4-12b "ps aux | head -20"
# root 1 /sbin/docker-init -- /datalab/run.sh
# root 125 /usr/bin/python3 /usr/local/bin/jupyter-server ...
# root 6241 /usr/bin/python3 -m colab_kernel_launcher ...
# root 110 sshd: /usr/sbin/sshd [listener]

# nvidia-smi works inside kernel, not host:
colab --auth=adc exec -s g-gemma-4-12b -f /tmp/check.py
# → +-----------------------------------------------------------------------------------------+
#   | GPU  Tesla T4  15360MiB | 3MiB / 15360MiB | 0% |
```

## VSCode Implication

Remote-SSH connects via the same `ProxyCommand` → host FS. Its integrated terminal will also show `cuda False`. To run GPU workloads from VSCode:

1. Keep a `colab exec` task: `colab --auth=adc exec -s g-gemma-4-12b -f script.py`
2. Or launch the kernel's python explicitly (not host's): the kernel's python is `/usr/bin/python3` inside the container, but host's python is a different mount. Simplest is to use `colab exec`.

## SSH ProxyCommand (must use `PYTHONPATH=` prefix)

```sshconfig
Host g-gemma-4-12b
  HostName colab-runtime
  User root
  ProxyCommand /usr/bin/env PYTHONPATH= /Users/rajivmehtapy/.local/share/uv/tools/mighty-colab/bin/mighty-colab ssh --proxy-mode -s g-gemma-4-12b
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  RequestTTY no
```

Without `/usr/bin/env PYTHONPATH=` the ProxyCommand inherits Hermes's `PYTHONPATH` and crashes with `ModuleNotFoundError: pydantic_core._pydantic_core` (Hermes uses Python 3.11 venv, colab uses 3.13).

## Checklist

- Always verify GPU via `colab exec`, never `ssh` alone
- If `ssh` shows `False` but `exec` shows `True`, that's expected — not a provisioning failure
- Don't install `openssh-server` manually; SSH is baked in at `colab new`
