# run_all.py
import sys
import subprocess
import time
from pathlib import Path
import os
from urllib.parse import urlparse

USAGE = "Usage: python run_all.py <START_URL> <MAX_DEPTH:int> <MAX_PAGES:int>"

if len(sys.argv) < 4:
    print(USAGE)
    sys.exit(1)

START_URL = sys.argv[1]
try:
    MAX_DEPTH = int(sys.argv[2])
    MAX_PAGES = int(sys.argv[3])
except ValueError:
    print(USAGE)
    sys.exit(1)

# ── NEW: Ensure Astra DB dynamically ─────────────────────────────────────────
from astra_db_manager import ensure_db
ensure_db(START_URL)   # sets env vars dynamically (DB + token)

# ---- Special-case: only fetch the Case Studies landing page, skip individual studies ----
CASE_STUDY_INDEX = "https://www.incede.ai/resources/case-studies"
if START_URL.rstrip("/") == CASE_STUDY_INDEX.rstrip("/"):
    if MAX_DEPTH != 0:
        print("ℹ️  Detected Case Studies index. Forcing MAX_DEPTH=0 to avoid crawling individual case studies.")
    MAX_DEPTH = 0  # do not follow links beneath the landing page

RUN_ID = time.strftime("%Y%m%d_%H%M%S")
BASE_DIR = Path("data") / RUN_ID
BASE_DIR.mkdir(parents=True, exist_ok=True)

# 🔑 Extract domain for SITE_NAME
parsed_url = urlparse(START_URL)
site_name = parsed_url.netloc or START_URL
os.environ["SITE_NAME"] = site_name

print(f"🚀 Starting pipeline | run_id: {RUN_ID}")
print(f"📂 Output dir: {BASE_DIR}")
print(f"🌐 SITE_NAME set to: {site_name}")
print(f"🔗 START_URL: {START_URL}")
print(f"🧭 MAX_DEPTH:  {MAX_DEPTH}")
print(f"📄 MAX_PAGES:  {MAX_PAGES}")

def run(pyfile: str, *args: str):
    """Run a Python script with the current interpreter; exit on failure."""
    cmd = [sys.executable, pyfile, *map(str, args)]
    print(f"\n=== Running: {' '.join(cmd)} ===")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"❌ Error running: {' '.join(cmd)}")
        sys.exit(r.returncode)

# 1) Crawl → writes data/<run_id>/{raw,parsed,master.json}
run("crawl.py", START_URL, MAX_DEPTH, MAX_PAGES, RUN_ID)

# 2) Detect page type
run("detect_page_type.py", RUN_ID)

# 3) Pick chunking strategy
run("detect_chunking_strategy.py", RUN_ID)

# 4) (FAISS step removed) — Astra-only pipeline

# 5) Ensure vector collection exists in this DB
run("create_astra_collection.py")

# 6) Upload parsed JSON + embeddings to Astra DB collection
run("upload_parsed_to_astra.py", RUN_ID)

# 7) Launch Astra-backed Q&A loop (RAG with Watsonx)
run("query_astra_llm.py", RUN_ID)

print(f"\n✅ Done | run_id: {RUN_ID} | Stored in: {BASE_DIR}")