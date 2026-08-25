# Deployment: systemd, Docker, Security

## systemd Service

```ini
# /etc/systemd/system/hermes-api.service
[Unit]
Description=Hermes Agent API Bridge
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=hermes
Group=hermes
WorkingDirectory=/opt/hermes-server
Environment=HERMES_API_CONFIG=/opt/hermes-server/config/server.yaml

ExecStart=/opt/hermes-server/.venv/bin/uvicorn api.main:app \
    --host 0.0.0.0 --port 8000 --workers 4

Restart=always
RestartSec=5

StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-api

[Install]
WantedBy=multi-user.target
```

Install:
```bash
sudo cp systemd/hermes-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hermes-api
sudo systemctl start hermes-api
sudo journalctl -u hermes-api -f   # view logs
```

## Docker Compose

```yaml
version: "3.8"
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["127.0.0.1:11434:11434"]
    volumes: [ollama-models:/root/.ollama]
    # GPU support:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: all
    #           capabilities: [gpu]

  hermes-api:
    build: .
    ports: ["0.0.0.0:8000:8000"]
    depends_on: [ollama]
    environment:
      - HERMES_API_CONFIG=/app/config/server.yaml
      - OLLAMA_HOST=http://ollama:11434
    volumes:
      - hermes-data:/root/.hermes
      - ./data:/app/data

volumes:
  ollama-models:
  hermes-data:
```

Dockerfile:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ripgrep ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY api/ ./api/
COPY config/requirements.txt ./config/requirements.txt
RUN pip install --no-cache-dir -r config/requirements.txt
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Security

### Network Exposure

```bash
# Firewall: LAN only
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw deny 8000
```

### Nginx TLS Reverse Proxy

```nginx
server {
    listen 443 ssl;
    server_name hermes.yourdomain.local;
    ssl_certificate /etc/ssl/certs/hermes.crt;
    ssl_certificate_key /etc/ssl/private/hermes.key;
    client_max_body_size 100M;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
    }
}
```

### Token Generation

```python
import secrets
token = secrets.token_urlsafe(32)
```

## Install Script (Debian)

```bash
#!/bin/bash
set -e

# System packages
sudo apt install -y git python3 python3-venv python3-pip \
    build-essential cmake pkg-config libssl-dev libffi-dev \
    curl wget ripgrep ffmpeg nodejs npm jq

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama && sudo systemctl start ollama
ollama pull qwen3.5:14b

# Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Configure
hermes config set model.provider custom
hermes config set model.default qwen3.5:14b
hermes config set model.base_url http://127.0.0.1:11434/v1

# API venv
cd /opt/hermes-server
python3 -m venv .venv
.venv/bin/pip install -r config/requirements.txt

# Generate token
TOKEN=$(.venv/bin/python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "API token: $TOKEN"
```
