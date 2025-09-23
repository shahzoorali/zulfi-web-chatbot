import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLL = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")

cl = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)\
     .get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)\
     .get_collection(COLL)

print("\n=== SAMPLE DOCUMENTS IN COLLECTION ===\n")
for d in cl.find({}, limit=5):  # just show 5 docs
    print("site_name:", d.get("site_name"))
    print("url:", d.get("url"))
    print("chunk_index:", d.get("chunk_index"))
    print("text preview:", (d.get("text") or "")[:200], "...\n")