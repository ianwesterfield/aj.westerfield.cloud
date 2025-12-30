"""Deploy AJ Filter to Open-WebUI."""
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
FILTER_PATH = ROOT / "filters" / "aj.filter.py"
BASE_URL = "http://localhost:8180"

# Read credentials
username = (ROOT / "secrets" / "webui_admin_username.txt").read_text().strip()
password = (ROOT / "secrets" / "webui_admin_password.txt").read_text().strip()

# Sign in to get token
auth_resp = requests.post(
    f"{BASE_URL}/api/v1/auths/signin",
    json={"email": username, "password": password}
)
if auth_resp.status_code != 200:
    print(f"Auth failed: {auth_resp.status_code} {auth_resp.text}")
    exit(1)

token = auth_resp.json().get("token")
if not token:
    print("No token in response")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Get existing filters
r = requests.get(f"{BASE_URL}/api/v1/functions/", headers=headers)
data = r.json()
print(f"API response type: {type(data)}")

# Handle both list and dict responses
if isinstance(data, dict):
    # Could be {"items": [...]} or error response
    items = data.get("items", [data]) if "detail" not in data else []
elif isinstance(data, list):
    items = data
else:
    items = []
    print(f"Unexpected response: {data}")

filters = [x for x in items if isinstance(x, dict) and x.get("name") in ("AJ Filter", "AJ")]

# Read filter content
content = FILTER_PATH.read_text(encoding="utf-8")

if filters:
    fid = filters[0]["id"]
    existing_meta = filters[0].get("meta", {})
    print(f"Updating filter {fid}...")
    r = requests.post(
        f"{BASE_URL}/api/v1/functions/id/{fid}/update",
        headers=headers,
        json={
            "id": fid,
            "name": filters[0].get("name", "AJ"),
            "content": content,
            "meta": existing_meta
        }
    )
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:500])
else:
    print("Filter not found in API response")
    print(f"Found items: {[x.get('name') for x in items if isinstance(x, dict)]}")
