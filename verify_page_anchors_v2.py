# verify_page_anchors_v2.py  (SCRIPT_VERSION=V2_PROJECTION_ONLY)
import os, sys
from collections import defaultdict
from urllib.parse import urldefrag
from dotenv import load_dotenv, find_dotenv
from astrapy import DataAPIClient

print(">> RUNNING verify_page_anchors_v2.py (V2_PROJECTION_ONLY)")

load_dotenv(find_dotenv(usecwd=True), override=True)

ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
TOKEN    = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLL     = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
SITE     = os.getenv("SITE_NAME", "incede-dev.netlify.app")

if not ENDPOINT or not TOKEN:
    raise SystemExit("❌ Missing ASTRA_DB_API_ENDPOINT or ASTRA_DB_APPLICATION_TOKEN")

TARGET = sys.argv[1] if len(sys.argv) > 1 else \
    "https://incede-dev.netlify.app/services/gen-ai-implementation#ai-powered-web-agent"
BASE, _ = urldefrag(TARGET)

cl = DataAPIClient(TOKEN).get_database_by_api_endpoint(ENDPOINT).get_collection(COLL)

# 1) STRICT exact match
exact = list(cl.find({"site_name": SITE, "url": TARGET}, limit=1000))
print(f"[EXACT] {TARGET} -> {len(exact)} chunk(s)")

# 2) Pull all chunks for this site (NOTE: projection=, not fields=)
pool = list(cl.find(
    {"site_name": SITE},
    projection={"url": 1, "chunk_index": 1, "text": 1},
    limit=10000
))

# Group by anchor
groups = defaultdict(list)
for d in pool:
    u = d.get("url")
    if isinstance(u, str) and (u == BASE or u.startswith(BASE + "#")):
        groups[u].append(d)

print(f"\n[GROUPS under BASE] {BASE}")
for u in sorted(groups.keys()):
    print(f"  {u} -> {len(groups[u])} chunk(s)")

# 3) Show sample
if exact:
    print("\n[SAMPLE from EXACT]")
    for d in sorted(exact, key=lambda x: x.get("chunk_index", 0))[:2]:
        print(f"- {d.get('url')} | chunk {d.get('chunk_index')}")
        print((d.get('text') or '')[:200], "...\n")
elif groups:
    print("\n[NEAREST EXISTING ANCHOR SAMPLE]")
    first_anchor = next((u for u in sorted(groups.keys()) if u != BASE), None)
    if first_anchor:
        for d in sorted(groups[first_anchor], key=lambda x: x.get("chunk_index", 0))[:2]:
            print(f"- {d.get('url')} | chunk {d.get('chunk_index')}")
            print((d.get('text') or '')[:200], "...\n")