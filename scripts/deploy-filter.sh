#!/bin/bash
# Deploy AJ filter to Open-WebUI
# Run from WSL: ./scripts/deploy-filter.sh

set -e

cd "$(dirname "$0")/.."

WEBUI_URL="${WEBUI_URL:-http://localhost:8180}"
API_KEY=$(cat secrets/webui_admin_api_key.txt | tr -d '\r\n')

if [ -z "$API_KEY" ]; then
    echo "[ERROR] No API key found in secrets/webui_admin_api_key.txt"
    exit 1
fi

echo "[INFO] Loading filter from filters/aj.filter.py..."
FILTER_CONTENT=$(cat filters/aj.filter.py)
FILTER_LENGTH=${#FILTER_CONTENT}
echo "[INFO] Filter size: $FILTER_LENGTH chars"

# Check if filter exists
echo "[INFO] Checking for existing filter..."
FILTER_ID=$(curl -s -X GET "$WEBUI_URL/api/v1/functions/" \
    -H "Authorization: Bearer $API_KEY" | \
    jq -r '.[] | select(.name == "AJ Filter" or .name == "AJ" or .id == "aj" or .id == "aj_filter") | .id' | head -1)

if [ -n "$FILTER_ID" ]; then
    echo "[OK] Found existing filter: $FILTER_ID"
    ENDPOINT="$WEBUI_URL/api/v1/functions/id/$FILTER_ID/update"
else
    echo "[INFO] Creating new filter..."
    ENDPOINT="$WEBUI_URL/api/v1/functions/create"
fi

# Build JSON payload
PAYLOAD=$(jq -n --arg content "$FILTER_CONTENT" '{content: $content}')

echo "[DEPLOY] Updating filter at $ENDPOINT..."
RESPONSE=$(curl -s -X POST "$ENDPOINT" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

# Check result
if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    NAME=$(echo "$RESPONSE" | jq -r '.name')
    echo "[OK] Filter deployed: $NAME"
else
    ERROR=$(echo "$RESPONSE" | jq -r '.detail // .')
    echo "[ERROR] Deploy failed: $ERROR"
    exit 1
fi

echo "[DONE] Filter updated. Check: $WEBUI_URL/admin/functions"
