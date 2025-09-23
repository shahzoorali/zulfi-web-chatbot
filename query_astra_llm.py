import os, sys, re, time
from typing import List, Dict, Any
from dotenv import load_dotenv
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
import requests

# ── Env ─────────────────────────────────────────────────────────────
load_dotenv()
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
COLLECTION_NAME = os.getenv("ASTRA_COLLECTION_NAME", "chatbot_chunks")

WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL")
MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")
IBM_API_KEY = os.getenv("IBM_API_KEY")

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else None
SITE_NAME = os.getenv("SITE_NAME", "unknown_site")

# Retrieval + re-rank tuning (safe defaults for laptop testing)
EMBEDDER_MODEL = os.getenv("EMBEDDER_MODEL", "all-mpnet-base-v2")
CANDIDATE_K = int(os.getenv("CANDIDATE_K", "40"))      # vector top-K (larger since we filter client-side)
FINAL_K = int(os.getenv("FINAL_K", "5"))               # return top-N after re-rank

# Cross-Encoder config (TinyBERT fast default; upgrade later on server)
CE_MODEL = os.getenv("CE_MODEL", "cross-encoder/ms-marco-TinyBERT-L-2-v2")
CE_MAX_LEN = int(os.getenv("CE_MAX_LEN", "256"))
CE_TIMEOUT_MS = int(os.getenv("CE_TIMEOUT_MS", "300"))  # CE budget per request

# ── Astra client ────────────────────────────────────────────────────
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection(COLLECTION_NAME)

# ── Embeddings ─────────────────────────────────────────────────────
embedder = SentenceTransformer(EMBEDDER_MODEL)

# ── Cross-Encoder (lazy load on first use) ─────────────────────────
_CE = None
def get_ce():
    global _CE
    if _CE is None:
        _CE = CrossEncoder(CE_MODEL, max_length=CE_MAX_LEN)
    return _CE

# ── Watsonx helpers ────────────────────────────────────────────────
def get_watsonx_token():
    if not IBM_API_KEY:
        raise RuntimeError("Missing IBM_API_KEY")
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": IBM_API_KEY},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def watsonx_chat_call(messages, *, temperature=0, max_tokens=600, timeout=60):
    if not WATSONX_URL or not WATSONX_PROJECT_ID:
        raise RuntimeError("Missing WATSONX_URL or WATSONX_PROJECT_ID")
    token = get_watsonx_token()
    url = f"{WATSONX_URL}/ml/v1/text/chat?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    body = {
        "project_id": WATSONX_PROJECT_ID,
        "model_id": MODEL_ID,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    r = requests.post(url, headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    content = ""
    if isinstance(j, dict) and j.get("choices"):
        msg = j["choices"][0].get("message", {})
        c = msg.get("content")
        if isinstance(c, str):
            content = c.strip()
        elif isinstance(c, list):
            content = "\n".join(blk.get("text", "") for blk in c if blk.get("type") == "text").strip()
    return content

# ── Auto-hybrid keyword extraction (query-driven) ──────────────────
STOPWORDS = {
    "the","a","an","and","or","of","for","to","in","on","at","by","with","from","about",
    "what","which","who","whom","whose","is","are","was","were","be","been","being",
    "do","does","did","can","could","should","would","may","might","will","shall",
    "we","our","us","you","your","they","their","it","its","this","that","these","those",
    "please","show","tell","give","list","explain","how","why","when"
}

def extract_query_terms(q: str) -> List[str]:
    q = q.strip()
    phrases = re.findall(r'"([^"]+)"', q)
    q_wo_quotes = re.sub(r'"[^"]+"', " ", q)
    raw = re.split(r"[^\w+]+", q_wo_quotes.lower())
    words = [w for w in raw if w and len(w) >= 3 and w not in STOPWORDS]
    phrases = [p.strip().lower() for p in phrases if p.strip()]
    seen, ordered = set(), []
    for token in phrases + words:
        if token not in seen:
            seen.add(token)
            ordered.append(token)
    return ordered[:10]

# ── Vector candidate search (no DB string operators) ───────────────
def vector_candidate_search(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    vec = embedder.encode(query_text).tolist()
    # Read environment variables at runtime
    site_name = os.getenv("SITE_NAME", "unknown_site")
    run_id = os.getenv("RUN_ID")
    
    # Only base filter by site/run; avoid unsupported $regex/$ilike
    base_filter: Dict[str, Any] = {"site_name": {"$eq": site_name}}
    if run_id:
        base_filter["run_id"] = {"$eq": run_id}
    find_kwargs = {
        "sort": {"$vector": vec},
        "limit": top_k,
        "projection": {"url": 1, "title": 1, "text": 1, "run_id": 1, "site_name": 1, "chunk_index": 1},
        "filter": base_filter,
    }
    return list(collection.find(**find_kwargs))

# ── Client-side keyword gate (hybrid without DB operators) ─────────
def keyword_gate(candidates: List[Dict[str, Any]], terms: List[str]) -> List[Dict[str, Any]]:
    if not candidates or not terms:
        return candidates
    require_all = len(terms) >= 2  # AND when 2+ strong terms; else OR
    out = []
    for c in candidates:
        t = (c.get("text") or "").lower()
        hits = sum(1 for term in terms if term in t)
        if (require_all and hits == len(terms)) or (not require_all and hits >= 1):
            out.append(c)
    # If gate filtered everything, fall back to original candidates
    return out if out else candidates

# ── Lightweight fallback scorer (if CE times out) ──────────────────
def keyword_overlap_score(query_terms: List[str], text: str) -> float:
    if not query_terms or not text:
        return 0.0
    t = text.lower()
    score = 0.0
    for term in query_terms:
        if " " in term:
            if term in t:
                score += 2.0
        else:
            if re.search(r"\b" + re.escape(term) + r"\b", t):
                score += 1.0
    return score

# ── Cross-Encoder re-rank with timeout/fallback ────────────────────
def rerank_candidates(question: str, candidates: List[Dict[str, Any]], query_terms: List[str]) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    pairs = []
    for c in candidates:
        txt = (c.get("text") or "")[:1200]
        pairs.append([question, txt])

    start = time.time()
    try:
        ce = get_ce()
        scores = ce.predict(pairs, convert_to_numpy=True)
        elapsed_ms = (time.time() - start) * 1000.0
        if elapsed_ms > CE_TIMEOUT_MS:
            raise TimeoutError(f"CE exceeded budget: {elapsed_ms:.1f} ms")
        for c, s in zip(candidates, scores):
            c["_rerank_score"] = float(s)
        return sorted(candidates, key=lambda x: x.get("_rerank_score", 0.0), reverse=True)
    except Exception:
        # Fallback: keyword overlap + tie-break on vector similarity
        scored = []
        for c in candidates:
            s_kw = keyword_overlap_score(query_terms, c.get("text", ""))
            s_vec = float(c.get("$similarity", 0.0))
            scored.append((s_kw, s_vec, c))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [c for _, __, c in scored]

# ── LLM answering ──────────────────────────────────────────────────
def answer_with_llm(question, docs):
    context = "\n\n".join(d.get("text", "") for d in docs)
    system_msg = (
        f"You are the voice of the organization represented by {SITE_NAME}. "
        "Whenever a user says 'you', it always refers to this organization, not to any client or case study mentioned. "
        "Respond in first-person plural. Only use the provided context; if unknown, say so."
    )
    user_text = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": [{"type": "text", "text": user_text}]},
    ]
    return watsonx_chat_call(messages, temperature=0, max_tokens=600)

# ── Orchestrator ───────────────────────────────────────────────────
def retrieve_and_answer(q: str) -> Dict[str, Any]:
    terms = extract_query_terms(q)
    # 1) vector candidates
    cands = vector_candidate_search(q, top_k=CANDIDATE_K)
    if not cands:
        return {"answer": "No results in Astra DB.", "sources": []}
    # 2) client-side keyword gate (hybrid)
    gated = keyword_gate(cands, terms)
    # 3) CE re-rank (fallback safe)
    ranked = rerank_candidates(q, gated, terms)
    top_docs = ranked[:FINAL_K]
    # 4) LLM answer
    ans = answer_with_llm(q, top_docs)
    return {"answer": ans or "(no content)", "sources": top_docs}

# ── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"💬 Using Astra collection: {COLLECTION_NAME}")
    print(f"🌐 site_name: {SITE_NAME}" + (f" | run_id={RUN_ID}" if RUN_ID else ""))
    print(f"🔎 embedder: {EMBEDDER_MODEL} | vector topK: {CANDIDATE_K} → final: {FINAL_K}")
    print(f"🎯 re-rank: {CE_MODEL} (max_len={CE_MAX_LEN}, timeout={CE_TIMEOUT_MS}ms)")

    while True:
        try:
            q = input("\nAsk: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() in {"exit", "quit"}:
            break

        out = retrieve_and_answer(q)
        print("\n--- Answer ---")
        print(out["answer"])

        print("\n--- Sources ---")
        for h in out["sources"]:
            sim = h.get("$similarity", 0.0)
            rer = h.get("_rerank_score", None)
            if rer is not None:
                print(f"{h.get('url')}  (vec={sim:.4f}, ce={rer:.4f})")
            else:
                print(f"{h.get('url')}  (vec={sim:.4f})")