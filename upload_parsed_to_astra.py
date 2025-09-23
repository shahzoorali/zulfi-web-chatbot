import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────────────
# Load .env
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLLECTION_NAME = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")

SITE_NAME = os.getenv("SITE_NAME", "unknown_site")

# ──────────────────────────────────────────────────────────────────────────────
# Handle run_id
# ──────────────────────────────────────────────────────────────────────────────
def get_latest_run_folder():
    data_dir = Path("data")
    runs = [
        d for d in data_dir.iterdir()
        if d.is_dir() and (d / "parsed").exists()
    ]
    if not runs:
        raise RuntimeError("No valid run folders found in data/") 
    return str(sorted(runs)[-1].name)

if len(sys.argv) > 1:
    RUN_ID = sys.argv[1]
else:
    RUN_ID = get_latest_run_folder()

BASE_DIR = Path("data") / RUN_ID
PARSED = BASE_DIR / "parsed"

if not PARSED.exists():
    raise RuntimeError(f"Parsed folder not found: {PARSED}")

# ──────────────────────────────────────────────────────────────────────────────
# Connect to Astra DB
# ──────────────────────────────────────────────────────────────────────────────
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection(COLLECTION_NAME)

# ──────────────────────────────────────────────────────────────────────────────
# Embedding model
# ──────────────────────────────────────────────────────────────────────────────
model = SentenceTransformer("all-mpnet-base-v2")

# ──────────────────────────────────────────────────────────────────────────────
# Chunking function
# ──────────────────────────────────────────────────────────────────────────────
def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

# ──────────────────────────────────────────────────────────────────────────────
# URL normalizer: treat hash anchors as path segments
# ──────────────────────────────────────────────────────────────────────────────
def anchor_to_path(u: str) -> str:
    if not u:
        return u
    if "#" in u:
        base, frag = u.split("#", 1)
        if frag:
            return base.rstrip("/") + "/" + frag
        return base
    return u

# ──────────────────────────────────────────────────────────────────────────────
# Upload with UPSERT
# ──────────────────────────────────────────────────────────────────────────────
print(f"📤 Uploading data from run_id: {RUN_ID} | site: {SITE_NAME}")

count = 0
for file_path in PARSED.glob("*.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = data.get("text", "")
    if not text.strip():
        continue

    # Apply chunking strategy
    chunks = chunk_text(text)

    # Normalized URL (anchor → path)
    url_raw = data.get("url")
    url = anchor_to_path(url_raw)

    # Insert/update each chunk
    for idx, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()

        # Unique key = site_name + url + chunk_index
        filter_key = {
            "site_name": SITE_NAME,
            "url": url,
            "chunk_index": idx
        }

        doc = {
            "run_id": RUN_ID,
            "site_name": SITE_NAME,
            "url": url,
            "title": data.get("title"),
            "page_type": data.get("page_type"),
            "chunk_index": idx,
            "chunking_strategy": "1200_bytes_with_200_overlap",
            "text": chunk,
            "$vector": embedding
        }

        collection.update_one(filter_key, {"$set": doc}, upsert=True)
        count += 1

print(f"✅ Uploaded/updated {count} documents to collection '{COLLECTION_NAME}' in Astra DB")