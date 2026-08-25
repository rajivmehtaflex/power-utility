# templates/Dockerfile — Docker build for the Hermes API bridge
#
# Build: docker build -t hermes-api .
# Run:   docker run -p 8000:8000 -v hermes-data:/root/.hermes hermes-api
#
# Note: This containers ONLY the API bridge. For Ollama, use docker-compose.yml
# or run Ollama separately on the host.

FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ripgrep ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy API code
COPY api/ ./api/
COPY config/requirements.txt ./config/requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r config/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
