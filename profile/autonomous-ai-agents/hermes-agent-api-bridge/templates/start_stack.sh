#!/bin/bash
# templates/start_stack.sh — Start the full Hermes server stack
#
# Starts Ollama, preloads model, starts Hermes API, verifies health.

set -e

echo "=== Starting Hermes Server Stack ==="

# 1. Start Ollama (if not running)
if ! systemctl is-active --quiet ollama; then
    echo "Starting Ollama..."
    sudo systemctl start ollama
    sleep 3
fi

# 2. Preload model
echo "Preloading model..."
curl -s http://127.0.0.1:11434/api/generate \
    -d '{"model":"qwen3.5:14b","keep_alive":"24h"}' > /dev/null

# 3. Start Hermes API
echo "Starting Hermes API..."
sudo systemctl start hermes-api

# 4. Verify
sleep 2
echo "Health check..."
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

echo ""
echo "=== Stack Ready ==="
echo "API:    http://$(hostname -I | awk '{print $1}'):8000"
echo "Model:  http://127.0.0.1:11434/v1/models"
echo ""
echo "Test:   curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{\"prompt\":\"Hello\"}'"
