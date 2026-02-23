# Orchestrator Service
# Agentic reasoning engine with task planning and parallel execution
# Includes embedded FunnelCloud Agent for localhost bootstrap

FROM python:3.11-slim

WORKDIR /app

# Install dependencies for orchestrator + FunnelCloud agent
RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  curl \
  libicu-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module (needed for logging_utils)
COPY shared /app/shared

# Copy application code
COPY orchestrator .

# ====== FunnelCloud Agent (embedded sidecar) ======
# Copy pre-built linux-x64 self-contained agent
COPY agents/FunnelCloud/publish-linux /app/funnelcloud-agent
RUN chmod +x /app/funnelcloud-agent/FunnelCloud.Agent

# Copy startup script and ensure LF line endings (Windows CRLF safety)
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Default model fallback (overridden by Open-WebUI selection)
ENV OLLAMA_MODEL=aj-deepseek-r1-32b

# FunnelCloud Agent config (runs as embedded sidecar)
ENV FUNNEL_AGENT_ID=orchestrator-agent
ENV FUNNEL_INSECURE=true

# Expose ports: orchestrator API + FunnelCloud agent
# 8004 = Orchestrator FastAPI
# 41420/udp = FunnelCloud Discovery (multicast)
# 41421 = FunnelCloud HTTP API (health, discover-peers)
# 41235 = FunnelCloud gRPC (task execution)
EXPOSE 8004 41420/udp 41421 41235

# Run startup script (starts agent + orchestrator)
CMD ["/app/start.sh"]
