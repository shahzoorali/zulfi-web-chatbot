# check_page_chunks.py
import os
import sys
from urllib.parse import urldefrag
from dotenv import load_dotenv, find_dotenv
from astrapy import DataAPIClient

# ── Env ─────────────────────────────────────────────────────────────
load_dotenv(find_dotenv(usecwd=True), override=True)

ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
TOKEN    = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLL     = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
SITE     = os.getenv("SITE_NAME", "incede-dev.netlify.app")

missing = [k for k, v in {
    "ASTRA_DB_API_ENDPOINT": ENDPOINT,
    "ASTRA_DB_APPLICATION_TOKEN": TOKEN,
}.items() if not v]
if missing:
    raise SystemExit(f"❌ Missing env vars: {', '.join(missing)}. Check your .env in the SAME folder and rerun.")

# ── Input URL ───────────────────────────────────────────────────────
URL = sys.argv[1] if len(sys.argv) > 1 else "https://incede-dev.netlify.app/services/gen-ai-implementation#gen"
BASE_URL, _ = urldefrag(URL)

print(f"Using endpoint: {ENDPOINT[:38]}...  token: {TOKEN[:12]}…  coll: {COLL}  site: {SITE}")
print(f"Target URL: {URL}")

# ── Connect ─────────────────────────────────────────────────────────
cl = DataAPIClient(TOKEN).get_database_by_api_endpoint(ENDPOINT).get_collection(COLL)

# ── Fetch helpers ───────────────────────────────────────────────────
def try_exact(u: str):
    return list(cl.find({"site_name": SITE, "url": u}, limit=500))

def scan_site():
    # Pull a bounded pool for the site and filter locally by URL prefix/anchor.
    # Increase limit if your site has >5000 chunks.
    return list(cl.find({"site_name": SITE}, limit=5000))

# ── Retrieval strategy (no $regex / $startswith) ────────────────────
docs = try_exact(URL)

if not docs:
    docs = try_exact(BASE_URL)

if not docs:
    pool = scan_site()
    docs = []
    for d in pool:
        u = d.get("url")
        if not isinstance(u, str):
            continue
        if u == BASE_URL or (u.startswith(BASE_URL) and u != BASE_URL):
            # includes BASE_URL#anything
            docs.append(d)

# ── Output ──────────────────────────────────────────────────────────
print(f"\nFound {len(docs)} chunks for {URL}\n")

if not docs:
    print("No chunks found. Tips:")
    print(f"- Verify SITE_NAME matches ingestion (current: {SITE})")
    print(f"- Verify collection name (current: {COLL})")
    print(f"- Try base URL without #fragment: {BASE_URL}")
    sys.exit(0)

docs_sorted = sorted(docs, key=lambda x: (x.get("url", ""), x.get("chunk_index", 0)))

current_url = None
for d in docs_sorted:
    u = d.get("url")
    if u != current_url:
        current_url = u
        print("—" * 72)
        print(current_url)
    print(f"Chunk {d.get('chunk_index')}:")
    txt = (d.get("text") or "")
    print((txt[:600] + ("..." if len(txt) > 600 else "")) + "\n")