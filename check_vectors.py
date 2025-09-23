import os
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv()
cl = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))\
     .get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))\
     .get_collection(os.getenv("ASTRA_COLLECTION_NAME","chatbot_chunks"))

SITE = os.getenv("SITE_NAME","incede-dev.netlify.app")
doc = cl.find_one({"site_name": SITE}, projection={"$vector":1})
vec = doc.get("$vector") if doc else None
print("Has doc:", bool(doc))
print("Has $vector:", vec is not None)
print("Vector length:", len(vec) if vec else None)