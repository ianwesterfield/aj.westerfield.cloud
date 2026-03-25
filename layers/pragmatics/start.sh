#!/bin/bash
# Pragmatics API startup script
# Waits for Ollama main model, then starts the API

set -e

echo "=========================================="
echo "Pragmatics Container Startup"
echo "=========================================="

# ====== Wait for Ollama Main Model ======
# Block until main Ollama instance is ready for memory summarization
OLLAMA_HOST="${OLLAMA_HOST:-localhost}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"
OLLAMA_MODEL="${OLLAMA_MODEL:-r1-distill-aj:32b-8k}"

echo "[1/2] Waiting for Ollama at $OLLAMA_URL with model $OLLAMA_MODEL..."
/app/shared/wait-for-ollama.sh "$OLLAMA_URL" "$OLLAMA_MODEL" 300

# Start Pragmatics API
echo "[2/2] Starting Pragmatics API..."
exec uvicorn server:app --host 0.0.0.0 --port 8001
