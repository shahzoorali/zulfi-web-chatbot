# create_astra_collection.py
import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLLECTION_NAME = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")

client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)

print("✅ Connected to Astra DB")

# list_collections may return objects or dicts
existing = []
for c in db.list_collections():
    if hasattr(c, "name"):
        existing.append(c.name)
    elif isinstance(c, dict) and "name" in c:
        existing.append(c["name"])

if COLLECTION_NAME not in existing:
    db.create_collection(
        COLLECTION_NAME,
        definition={
            "vector": {
                "dimension": 768,   # all-mpnet-base-v2
                "metric": "cosine"
            }
        }
    )
    print(f"📦 Created vector collection: {COLLECTION_NAME}")
else:
    print(f"ℹ️ Collection already exists: {COLLECTION_NAME}")