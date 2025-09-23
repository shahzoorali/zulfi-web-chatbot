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

for d in cl.find({}, limit=5, projection={"site_name":1}):
    print(d.get("site_name"))