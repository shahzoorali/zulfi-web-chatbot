import asyncio, hashlib, json, re, sys, time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

RAW = Path("data/raw"); PARSED = Path("data/parsed"); MASTER = Path("data/master.json")
RAW.mkdir(parents=True, exist_ok=True); PARSED.mkdir(parents=True, exist_ok=True)

def slug(url:str)->str:
    host = re.sub(r"^https?://","",url).split("/")[0]
    h = hashlib.md5(url.encode()).hexdigest()[:10]
    return f"{host}_{h}"

def extract(html:str):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    text = " ".join(soup.get_text(" ").split())
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"): 
            continue
        links.append(href)
    return title, text, links

async def fetch(url:str):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context()
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        html = await page.content()
        await b.close()
    return html

def save_individual(url:str, html:str, title:str, text:str, links:list[str]):
    name = slug(url)
    (RAW / f"{name}.html").write_text(html, encoding="utf-8")
    item = {
        "id": name,
        "url": url,
        "title": title,
        "timestamp": int(time.time()),
        "text": text,
        "links": links,
    }
    (PARSED / f"{name}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return item

def rebuild_master():
    all_items = []
    for p in PARSED.glob("*.json"):
        try:
            all_items.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    MASTER.write_text(json.dumps({"count": len(all_items), "items": all_items}, ensure_ascii=False, indent=2), encoding="utf-8")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_one.py <URL>")
        sys.exit(1)
    url = sys.argv[1]
    html = await fetch(url)
    title, text, links = extract(html)
    item = save_individual(url, html, title, text, links)
    rebuild_master()
    print(f"Saved: data/parsed/{item['id']}.json")
    print(f"Updated: data/master.json  (count={len(json.loads(MASTER.read_text(encoding='utf-8'))['items'])})")

if __name__ == "__main__":
    asyncio.run(main())