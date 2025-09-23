import os
import re
import json
import glob
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# ──────────────────────────────────────────────────────────────────────────────
# Env & Config
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

IBM_API_KEY = os.getenv("IBM_API_KEY")
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
PROMPT_TEMPLATE = """You are a website analysis assistant.
Given the page text, identify:
1. Page type (e.g., Homepage, Services, Products, Case Studies, About, Contact)
2. Reasoning for classification.

Text:
---
{text}
---

Respond in JSON:
{{"page_type": "...", "reason": "..."}}
"""

# ──────────────────────────────────────────────────────────────────────────────
def get_watsonx_token():
    if not IBM_API_KEY:
        raise RuntimeError("Missing IBM_API_KEY")
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_API_KEY,
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
                "content": "Return only one JSON object with keys page_type and reason; nothing else.",
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

def detect_page_type(text: str):
    prompt = PROMPT_TEMPLATE.format(text=(text or "")[:4000])
    out = watsonx_chat_call(prompt, temperature=0, max_tokens=500)
    content = out["text"]

    # Try direct JSON
    if content.startswith("{") and content.endswith("}"):
        try:
            parsed = json.loads(content)
            return {
                "page_type": parsed.get("page_type", "Unknown"),
                "reason": parsed.get("reason", ""),
            }
        except Exception:
            pass

    # Try code fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
    if fence:
        candidate = fence.group(1).strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                parsed = json.loads(candidate)
                return {
                    "page_type": parsed.get("page_type", "Unknown"),
                    "reason": parsed.get("reason", ""),
                }
            except Exception as e:
                return {"page_type": "Unknown", "reason": f"JSON parse error: {e}"}

    # Fallback: first JSON object
    candidate = _extract_first_json_object(content)
    if candidate:
        try:
            parsed = json.loads(candidate)
            return {
                "page_type": parsed.get("page_type", "Unknown"),
                "reason": parsed.get("reason", ""),
            }
        except Exception as e:
            return {"page_type": "Unknown", "reason": f"JSON parse error: {e}"}

    return {"page_type": "Unknown", "reason": "No valid JSON found in model output."}

def main():
    files = sorted(glob.glob(str(PARSED / "*.json")))
    if not files:
        print(f"No JSON files found in {PARSED.resolve()}")
        return

    for f in files:
        p = Path(f)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[SKIP] {p.name}: invalid JSON ({e})")
            continue

        if "page_type" in data and "reason" in data:
            continue

        url = data.get("url", p.name)
        text = data.get("text", "")
        if not text:
            print(f"[SKIP] {url}: no 'text' field")
            continue

        print(f"Processing: {url}")
        result = detect_page_type(text)
        data.update(result)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ detect_page_type completed for run {RUN_ID}")

if __name__ == "__main__":
    main()