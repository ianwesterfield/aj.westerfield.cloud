#!/bin/bash
# Orchestrator startup script
# Starts embedded FunnelCloud agent as sidecar, then the orchestrator API

set -e

echo "=========================================="
echo "Orchestrator Container Startup"
echo "=========================================="

# Start FunnelCloud Agent (sidecar) in background
echo "[1/2] Starting FunnelCloud Agent..."
cd /app/funnelcloud-agent

# Set agent environment
export FUNNEL_AGENT_ID="${FUNNEL_AGENT_ID:-orchestrator-agent}"
export FUNNEL_DISCOVERY_PORT="${FUNNEL_DISCOVERY_PORT:-41420}"
export FUNNEL_GRPC_PORT="${FUNNEL_GRPC_PORT:-41235}"
export FUNNEL_HTTP_PORT="${FUNNEL_AGENT_HTTP_PORT:-41421}"

./FunnelCloud.Agent &
AGENT_PID=$!
echo "    FunnelCloud Agent started (PID: $AGENT_PID)"

# Give agent time to start and bind ports
sleep 2

# Verify agent is running
if ! kill -0 $AGENT_PID 2>/dev/null; then
    echo "ERROR: FunnelCloud Agent failed to start!"
    exit 1
fi

# Check agent health endpoint
echo "    Checking agent health..."
for i in {1..5}; do
    if curl -s http://localhost:${FUNNEL_HTTP_PORT}/health > /dev/null 2>&1; then
        echo "    Agent health check passed!"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "WARNING: Agent health check failed (continuing anyway)"
    fi
    sleep 1
done

# Start Orchestrator API (foreground)
echo "[2/2] Starting Orchestrator API..."
cd /app
exec uvicorn main:app --host 0.0.0.0 --port 8004
