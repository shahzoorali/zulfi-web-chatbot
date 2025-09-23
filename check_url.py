import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()
cl = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))\
     .get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))\
     .get_collection(os.getenv("ASTRA_COLLECTION_NAME","chatbot_chunks"))

SITE = os.getenv("SITE_NAME","incede-dev.netlify.app")
needle = "services/planning-budgeting-and-analytics"

seen=set()
for d in cl.find({"site_name": SITE}, limit=3000, projection={"url":1}):
    u = (d.get("url") or "")
    if needle in u and u not in seen:
        seen.add(u); print(u)

print("\nTotal matches:", len(seen))