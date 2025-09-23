# verify_page_anchors.py
import os, sys
from collections import defaultdict
from urllib.parse import urldefrag
from dotenv import load_dotenv, find_dotenv
from astrapy import DataAPIClient

load_dotenv(find_dotenv(usecwd=True), override=True)

ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
TOKEN    = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLL     = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
SITE     = os.getenv("SITE_NAME", "incede-dev.netlify.app")

if not ENDPOINT or not TOKEN:
    raise SystemExit("❌ Missing ASTRA_DB_API_ENDPOINT or ASTRA_DB_APPLICATION_TOKEN")

TARGET = sys.argv[1] if len(sys.argv) > 1 else "https://incede-dev.netlify.app/services/gen-ai-implementation#ai-powered-web-agent"
BASE, _ = urldefrag(TARGET)

cl = DataAPIClient(TOKEN).get_database_by_api_endpoint(ENDPOINT).get_collection(COLL)

# 1) STRICT exact match — no fallback.
exact = list(cl.find({"site_name": SITE, "url": TARGET}, limit=1000))
print(f"[EXACT] {TARGET} -> {len(exact)} chunk(s)")

# 2) Group all chunks under BASE and its anchors (client-side).
pool = list(cl.find({"site_name": SITE}, fields={"url":1,"chunk_index":1,"text":1}, limit=10000))
groups = defaultdict(list)
for d in pool:
    u = d.get("url")
    if isinstance(u, str) and (u == BASE or u.startswith(BASE + "#")):
        groups[u].append(d)

print(f"\n[GROUPS under BASE] {BASE}")
for u in sorted(groups.keys()):
    print(f"  {u} -> {len(groups[u])} chunk(s)")

# 3) If exact exists, show a quick sample; else show closest anchor present
if exact:
    print("\n[SAMPLE from EXACT]")
    for d in sorted(exact, key=lambda x: x.get("chunk_index", 0))[:2]:
        print(f"- {d.get('url')} | chunk {d.get('chunk_index')}")
        print((d.get('text') or '')[:200], "...\n")
else:
    # show top 2 chunks from #gen if that's what exists
    for u in sorted(groups.keys()):
        if u != BASE:
            print("\n[NEAREST EXISTING ANCHOR SAMPLE]")
            for d in sorted(groups[u], key=lambda x: x.get("chunk_index", 0))[:2]:
                print(f"- {d.get('url')} | chunk {d.get('chunk_index')}")
                print((d.get('text') or '')[:200], "...\n")
            break