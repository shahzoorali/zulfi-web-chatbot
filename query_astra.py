import os
import sys
from dotenv import load_dotenv
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────────────
# Load .env file
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLLECTION_NAME = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")

# ──────────────────────────────────────────────────────────────────────────────
# Optional run_id filter
# ──────────────────────────────────────────────────────────────────────────────
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else None

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

def search_astra(query_text, top_k=5):
    embedding = model.encode(query_text).tolist()

    search_params = {
        "vector": embedding,
        "limit": top_k
    }
    if RUN_ID:
        search_params["filter"] = {"run_id": {"$eq": RUN_ID}}

    results = collection.find(**search_params)

    return results

# ──────────────────────────────────────────────────────────────────────────────
# CLI loop
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"💬 Connected to Astra DB collection: {COLLECTION_NAME}")
    if RUN_ID:
        print(f"🔍 Filtering by run_id: {RUN_ID}")

    while True:
        try:
            query = input("\nAsk: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query or query.lower() in {"exit", "quit"}:
            break

        results = search_astra(query, top_k=5)
        print("\n--- Results ---")
        for r in results:
            print(f"[score: {r.get('$similarity', 0):.4f}] {r.get('url')}")
            print(f"Title: {r.get('title')}")
            print(f"Snippet: {r.get('text')[:200]}...\n")
