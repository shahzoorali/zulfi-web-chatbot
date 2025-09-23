import os
import json
import glob
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# ──────────────────────────────────────────────────────────────────────────────
# Env & Config
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL = os.getenv("WATSONX_URL")  # e.g., https://ca-tor.ml.cloud.ibm.com
MODEL_ID = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

# ──────────────────────────────────────────────────────────────────────────────
# Handle run_id
# ──────────────────────────────────────────────────────────────────────────────
def get_latest_run_folder():
    data_dir = Path("data")
    runs = [d for d in data_dir.iterdir() if d.is_dir()]
    if not runs:
        raise RuntimeError("No run folders found in data/")
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
STRATEGIES = [
    "DOM + Intent-Based",
    "Question-Driven + Token-Based",
    "Token-Based (Sliding)",
    "Token + Paragraph Mapping",
    "Manual"
]

PROMPT_TEMPLATE = """You are an expert in website content chunking for vector databases.
Given:
- Page type: {page_type}
- Text content: {text}

Choose the best chunking strategy from this list (return only one):
{strategies}

Explain briefly WHY this strategy is best for this page type and content.

Respond in JSON exactly as:
{{"chunking_strategy": "...", "reasoning": "..."}}
"""

# ──────────────────────────────────────────────────────────────────────────────
def get_watsonx_token():
    apikey = os.getenv("IBM_API_KEY")
    if not apikey:
        raise RuntimeError("Missing IBM_API_KEY")
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": apikey,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def watsonx_chat_call(prompt_text: str, *, temperature: float = 0, max_tokens: int = 500) -> dict:
    if not WATSONX_URL or not WATSONX_PROJECT_ID:
        raise RuntimeError("Missing WATSONX_URL or WATSONX_PROJECT_ID")

    token = get_watsonx_token()
    url = f"{WATSONX_URL}/ml/v1/text/chat?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {
        "project_id": WATSONX_PROJECT_ID,
        "model_id": MODEL_ID,
        "messages": [
            {
                "role": "system",
                "content": "Return only one JSON object with keys chunking_strategy and reasoning; nothing else.",
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}],
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    result = resp.json()

    # Extract content
    content = ""
    if isinstance(result, dict) and result.get("choices"):
        msg = result["choices"][0].get("message", {})
        c = msg.get("content")
        if isinstance(c, str):
            content = c.strip()
        elif isinstance(c, list):
            texts = [blk.get("text", "") for blk in c if isinstance(blk, dict) and blk.get("type") == "text"]
            content = "\n".join(texts).strip()

    return {"raw": result, "text": content}

def _extract_first_json_object(s: str):
    if not s:
        return None
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start: i + 1]
    return None

def detect_strategy(page_type: str, text: str):
    prompt = PROMPT_TEMPLATE.format(
        page_type=page_type or "Unknown",
        text=(text or "")[:4000],
        strategies="\n".join(STRATEGIES),
    )
    out = watsonx_chat_call(prompt, temperature=0, max_tokens=500)
    content = out["text"]

    # Try direct JSON
    if content.startswith("{") and content.endswith("}"):
        try:
            parsed = json.loads(content)
            return {
                "chunking_strategy": parsed.get("chunking_strategy", "Unknown"),
                "reasoning": parsed.get("reasoning", "")
            }
        except Exception:
            pass

    # Try code fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if fence:
        cand = fence.group(1).strip()
        if cand.startswith("{") and cand.endswith("}"):
            try:
                parsed = json.loads(cand)
                return {
                    "chunking_strategy": parsed.get("chunking_strategy", "Unknown"),
                    "reasoning": parsed.get("reasoning", "")
                }
            except Exception as e:
                return {"chunking_strategy": "Unknown", "reasoning": f"JSON parse error: {e}"}

    # Fallback: first JSON object
    cand = _extract_first_json_object(content)
    if cand:
        try:
            parsed = json.loads(cand)
            return {
                "chunking_strategy": parsed.get("chunking_strategy", "Unknown"),
                "reasoning": parsed.get("reasoning", "")
            }
        except Exception as e:
            return {"chunking_strategy": "Unknown", "reasoning": f"JSON parse error: {e}"}

    return {"chunking_strategy": "Unknown", "reasoning": "No valid JSON found in model output."}

def main():
    files = glob.glob(str(PARSED / "*.json"))
    if not files:
        print(f"No JSON files found in {PARSED.resolve()}")
        return

    for f in files:
        p = Path(f)
        data = json.loads(p.read_text(encoding="utf-8"))
        if "chunking_strategy" in data and "reasoning" in data:
            continue
        print(f"Processing: {data.get('url', p.name)}")
        info = detect_strategy(data.get("page_type", "Unknown"), data.get("text", ""))
        print(f"  Strategy: {info['chunking_strategy']}")
        print(f"  Reason: {info['reasoning']}\n")
        data.update(info)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ detect_chunking_strategy completed for run {RUN_ID}")

if __name__ == "__main__":
    main()