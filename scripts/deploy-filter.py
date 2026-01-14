#!/usr/bin/env python3
"""
Deploy AJ filter to Open-WebUI via API.

Usage:
    python scripts/deploy-filter.py
    # Or from WSL:
    wsl -d Debian python3 /mnt/c/Code/aj.westerfield.cloud/scripts/deploy-filter.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
FILTER_PATH = PROJECT_ROOT / "filters" / "aj.filter.py"
SECRET_PATH = PROJECT_ROOT / "secrets" / "webui_admin_api_key.txt"

# Config
WEBUI_URL = os.environ.get("WEBUI_URL", "http://localhost:8180")


def main():
    # Load API key
    if not SECRET_PATH.exists():
        print(f"[ERROR] API key not found: {SECRET_PATH}")
        sys.exit(1)
    
    api_key = SECRET_PATH.read_text().strip()
    if not api_key:
        print("[ERROR] API key is empty")
        sys.exit(1)
    
    # Load filter content
    if not FILTER_PATH.exists():
        print(f"[ERROR] Filter not found: {FILTER_PATH}")
        sys.exit(1)
    
    filter_content = FILTER_PATH.read_text(encoding="utf-8")
    print(f"[INFO] Loaded filter: {len(filter_content)} chars")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Find existing filter
    print("[INFO] Checking for existing AJ filter...")
    try:
        req = urllib.request.Request(
            f"{WEBUI_URL}/api/v1/functions/",
            headers=headers,
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            functions = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"[ERROR] Cannot connect to Open-WebUI: {e}")
        sys.exit(1)
    
    # Find AJ filter
    filter_id = None
    for f in functions:
        if f.get("name") in ("AJ", "AJ Filter") or f.get("id") in ("aj", "aj_filter"):
            filter_id = f["id"]
            print(f"[OK] Found existing filter: {filter_id}")
            break
    
    if filter_id:
        endpoint = f"{WEBUI_URL}/api/v1/functions/id/{filter_id}/update"
    else:
        print("[INFO] Creating new filter...")
        endpoint = f"{WEBUI_URL}/api/v1/functions/create"
    
    # Prepare payload (meta field is required by Open-WebUI API)
    payload = json.dumps({
        "id": filter_id or "aj",
        "name": "AJ",
        "content": filter_content,
        "meta": {
            "description": "AJ - Agentic reasoning & memory filter"
        }
    }).encode("utf-8")
    
    # Deploy
    print(f"[DEPLOY] POST {endpoint}")
    try:
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"[OK] Filter deployed: {result.get('name', result.get('id'))}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        print(f"[ERROR] Deploy failed ({e.code}): {error_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)
    
    print(f"[DONE] Check: {WEBUI_URL}/admin/functions")


if __name__ == "__main__":
    main()
