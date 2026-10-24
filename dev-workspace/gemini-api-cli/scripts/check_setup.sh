#!/usr/bin/env bash
# Preflight for the gemini-api-cli skill: verifies the CLI binary, reports the
# version, and checks that authentication is resolvable. Prints remediation
# steps; never installs or mutates anything itself.
#
# Exit codes: 0 = ready · 1 = missing binary · 2 = auth not resolvable

set -u

INSTALL_HINT='Install (macOS/Linux):
  curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api/main/scripts/install.sh | bash
Or with Go:  go install github.com/google-gemini/gemini-api-cli/cmd/gemini-api@latest
Windows (PowerShell):
  iwr -useb https://raw.githubusercontent.com/google-gemini/gemini-api/main/scripts/install.ps1 | iex'

if ! command -v gemini-api >/dev/null 2>&1; then
  echo "ERROR: 'gemini-api' not found on PATH." >&2
  echo "$INSTALL_HINT" >&2
  exit 1
fi

echo "binary:   $(command -v gemini-api)"
echo "version:  $(gemini-api version 2>/dev/null || echo unknown)"

# Auth check: env var is the common case; otherwise ask the CLI what it sees.
if [ -n "${GEMINI_API_KEY:-}" ]; then
  echo "auth:     GEMINI_API_KEY is set"
  exit 0
fi

# `whoami` reports resolved auth/global params without making an API call.
if auth_line="$(gemini-api whoami 2>/dev/null)"; then
  echo "auth:     resolved by CLI (keychain or config file)"
  exit 0
fi

echo "auth:     WARNING - no GEMINI_API_KEY in env, and no stored credentials found." >&2
echo "Fix one of:" >&2
echo "  export GEMINI_API_KEY=\"your-key\"        # from https://aistudio.google.com" >&2
echo "  gemini-api configure --api-key \"your-key\" # stores in OS keychain" >&2
exit 2
