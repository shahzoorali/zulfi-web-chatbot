import os
from dotenv import load_dotenv
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer

load_dotenv()
cl = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))\
     .get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))\
     .get_collection(os.getenv("ASTRA_COLLECTION_NAME","chatbot_chunks"))

SITE = os.getenv("SITE_NAME","incede-dev.netlify.app")
URL = "https://incede-dev.netlify.app/services/gen-ai-implementation/custom-foundation-model-training"

# encode query
model = SentenceTransformer("all-mpnet-base-v2")
q = "What models does incede support?"
qvec = model.encode(q).tolist()

# run ANN query restricted to this page only
docs = cl.find({"site_name": SITE, "url": URL},
               sort={"$vector": qvec}, limit=5,
               projection={"url":1,"chunk_index":1,"text":1})

print("\n=== Top Results ===")
for i,d in enumerate(docs):
    print(f"[{i}] url={d.get('url')} chunk={d.get('chunk_index')}")
    print((d.get("text") or "")[:250], "...\n")