#!/bin/bash
# Pragmatics API startup script
# Waits for Ollama facts model, then starts the API

set -e

echo "=========================================="
echo "Pragmatics Container Startup"
echo "=========================================="

# ====== Wait for Ollama Facts Model ======
# Block until ollama-facts instance has the extraction model loaded
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11436}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"
FACT_MODEL="${FACT_EXTRACTION_MODEL:-qwen2.5:1.5b}"

echo "[1/2] Waiting for Ollama facts model..."
/app/shared/wait-for-ollama.sh "$OLLAMA_URL" "$FACT_MODEL" 300

# Start Pragmatics API
echo "[2/2] Starting Pragmatics API..."
exec uvicorn server:app --host 0.0.0.0 --port 8001
