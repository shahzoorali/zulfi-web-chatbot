# probe_and_prompt_debug.py
import os, textwrap, sys
from dotenv import load_dotenv
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer

load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLL = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")
SITE = os.getenv("SITE_NAME", "unknown_site")

missing = [k for k,v in {
    "ASTRA_DB_API_ENDPOINT":ASTRA_DB_API_ENDPOINT,
    "ASTRA_DB_APPLICATION_TOKEN":ASTRA_DB_APPLICATION_TOKEN,
}.items() if not v]
if missing:
    print("Missing env vars:", ", ".join(missing))
    sys.exit(1)

QUESTION = "What is AI Roadmapping at Incede?"
TOP_K = 6

model = SentenceTransformer("all-mpnet-base-v2")
qvec = model.encode(QUESTION).tolist()

cl = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)\
     .get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)\
     .get_collection(COLL)

docs = cl.find({"site_name": SITE}, sort={"$vector": qvec}, limit=TOP_K,
               projection={"url":1,"title":1,"text":1,"chunk_index":1})

print("\n[RETRIEVED CHUNKS]")
ctx_blocks = []
for i, d in enumerate(docs):
    txt = (d.get("text","") or "").strip().replace("\n"," ")
    print(f"[{i}] url={d.get('url')}  chunk={d.get('chunk_index')}")
    print(textwrap.shorten(txt, 300)); print("-"*60)
    ctx_blocks.append(f"[Source {i}] {d.get('url')}\n{d.get('text','')}")

prompt = f"""Answer strictly from CONTEXT. If not found, say "Not found in site content."
QUESTION: {QUESTION}

CONTEXT:
{chr(10).join(ctx_blocks)}
"""
print("\n[FINAL PROMPT SENT TO LLM]\n"); print(prompt)