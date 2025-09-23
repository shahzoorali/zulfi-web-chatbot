# astra_db_manager.py
import os, sys, time, requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

ASTRA_DEVOPS_TOKEN = os.getenv("ASTRA_DEVOPS_TOKEN")  # an existing org-scoped token that can create tokens
ASTRA_ORG_ID = os.getenv("ASTRA_ORG_ID")              # recommended
ASTRA_REGION = os.getenv("ASTRA_REGION", "us-east-2")
ASTRA_CLOUD = os.getenv("ASTRA_CLOUD", "AWS")
ASTRA_TIER = os.getenv("ASTRA_TIER", "serverless")
ASTRA_DB_TYPE = os.getenv("ASTRA_DB_TYPE", "vector")

if not ASTRA_DEVOPS_TOKEN:
    raise RuntimeError("Missing ASTRA_DEVOPS_TOKEN in .env")

DEVOPS_BASE = "https://api.astra.datastax.com/v2"

def _headers():
    h = {"Authorization": f"Bearer {ASTRA_DEVOPS_TOKEN}", "Content-Type": "application/json"}
    if ASTRA_ORG_ID:
        h["X-DataStax-Current-Org"] = ASTRA_ORG_ID
    return h

def extract_db_name(start_url: str) -> str:
    netloc = urlparse(start_url).netloc or start_url
    netloc = netloc.split(":")[0].lower()
    if netloc.startswith("www."): netloc = netloc[4:]
    parts = netloc.split(".")
    candidate = parts[-2] if len(parts) >= 2 else netloc
    clean = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in candidate).strip("-")
    return clean or "site-db"

# ── DB lifecycle ──────────────────────────────────────────────────────────────
def list_dbs():
    r = requests.get(f"{DEVOPS_BASE}/databases", headers=_headers(), timeout=30)
    r.raise_for_status()
    body = r.json()
    return body["data"] if isinstance(body, dict) and "data" in body else body

def find_existing_db(name: str):
    for db in list_dbs() or []:
        info = db.get("info", {}) or {}
        if (info.get("name") or db.get("name")) == name:
            return db
    return None

def get_db(db_id: str):
    r = requests.get(f"{DEVOPS_BASE}/databases/{db_id}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()

def wait_for_active(db_id: str):
    for _ in range(40):
        db = get_db(db_id)
        status = db.get("status") or (db.get("info", {}) or {}).get("status")
        print(f"⏳ DB status: {status}")
        if status == "ACTIVE":
            return db
        time.sleep(15)
    raise RuntimeError("DB did not become ACTIVE in time")

def poll_find_by_name(name: str, attempts=60, delay=5):
    for _ in range(attempts):
        db = find_existing_db(name)
        if db: return db
        time.sleep(delay)
    raise RuntimeError(f"DB '{name}' not visible after create")

def create_db(name: str):
    payload = {
        "name": name,
        "keyspace": "default_keyspace",
        "cloudProvider": ASTRA_CLOUD,
        "tier": ASTRA_TIER,
        "capacityUnits": 1,
        "region": ASTRA_REGION,
        "dbType": ASTRA_DB_TYPE,  # "vector"
    }
    r = requests.post(f"{DEVOPS_BASE}/databases", headers=_headers(), json=payload, timeout=60)
    if r.status_code in (200, 201, 202, 409):
        return poll_find_by_name(name)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        raise RuntimeError(f"Create DB failed ({r.status_code}): {r.text[:400]}") from None

# ── Token via /v2/tokens (org-scoped) ─────────────────────────────────────────
def list_roles():
    r = requests.get(f"{DEVOPS_BASE}/organizations/roles", headers=_headers(), timeout=30)
    r.raise_for_status()
    body = r.json()
    return body["data"] if isinstance(body, dict) and "data" in body else body

def get_role_id_by_name(name: str):
    for role in list_roles() or []:
        if role.get("name") == name:
            return role.get("id")
    return None

def create_app_token_for_org(role_name="Organization Administrator", description="Auto-minted by pipeline"):
    role_id = get_role_id_by_name(role_name)
    if not role_id:
        # fallback to Database Administrator if Org Admin not found
        role_id = get_role_id_by_name("Database Administrator")
    if not role_id:
        raise RuntimeError("Could not resolve a suitable role id (need 'Organization Administrator' or 'Database Administrator').")

    payload = {
        "roles": [role_id],
        "description": description
        # "tokenExpiry": "2027-01-01T00:00:00Z"  # optional
    }
    # Org may be inferred from header; include explicit orgId if available
    if ASTRA_ORG_ID:
        payload["orgId"] = ASTRA_ORG_ID

    r = requests.post(f"{DEVOPS_BASE}/tokens", headers=_headers(), json=payload, timeout=60)
    r.raise_for_status()
    body = r.json() if r.content else {}
    token = body.get("token")
    if not token:
        raise RuntimeError(f"Token mint failed: {body or r.text[:400]}")
    return token

# ── Public entrypoint ─────────────────────────────────────────────────────────
def ensure_db(start_url: str):
    db_name = extract_db_name(start_url)
    print(f"🔎 Checking Astra DB for '{db_name}'...")
    db = find_existing_db(db_name)
    if not db:
        print(f"📦 Creating new Astra DB: {db_name}")
        db = create_db(db_name)

    db_id = db.get("id") or (db.get("info", {}) or {}).get("id")
    if not db_id:
        raise RuntimeError("Could not determine DB id from response")

    db = wait_for_active(db_id)
    info = db.get("info", {}) or {}
    endpoint = info.get("dataEndpoint") or db.get("dataEndpoint") or f"https://{db_id}-{ASTRA_REGION}.apps.astra.datastax.com"
    print(f"✅ Astra DB ready: {db_name} | endpoint: {endpoint}")

    # Mint an application token (org-scoped role; works for Data API)
    app_token = create_app_token_for_org(description=f"Pipeline token for {db_name}")
    print("🔑 Application token minted")

    os.environ["ASTRA_DB_API_ENDPOINT"] = endpoint
    os.environ["ASTRA_DB_APPLICATION_TOKEN"] = app_token
    os.environ["ASTRA_COLLECTION_NAME"] = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
    os.environ["ASTRA_KEYSPACE"] = os.getenv("ASTRA_KEYSPACE", "default_keyspace")
    return endpoint, app_token

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python astra_db_manager.py <START_URL>")
        sys.exit(1)
    ensure_db(sys.argv[1])