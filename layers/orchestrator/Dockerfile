# Orchestrator Service
# Agentic reasoning engine with task planning and parallel execution

FROM python:3.11-slim

WORKDIR /app

# Install git for cloning workspaces
RUN apt-get update && apt-get install -y --no-install-recommends git \
  && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module (needed for logging_utils)
COPY shared /app/shared

# Copy application code
COPY orchestrator . .

# Set Ollama model - llama3.1:70b is much better at JSON format compliance than qwen
ENV OLLAMA_MODEL=llama3.1:70b

# Expose port
EXPOSE 8004

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
