# crawl.py
import os
import asyncio, hashlib, json, re, sys, time, urllib.parse
from pathlib import Path
from collections import deque
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Run ID & folders
# ──────────────────────────────────────────────────────────────────────────────
def get_run_id_from_args():
    if len(sys.argv) >= 5:
        return sys.argv[4]  # run_id passed from run_all.py or chatbot backend
    return time.strftime("%Y%m%d_%H%M%S")  # default: generate new

RUN_ID = get_run_id_from_args()
BASE_DIR = Path("data") / RUN_ID
RAW = BASE_DIR / "raw"
PARSED = BASE_DIR / "parsed"
MASTER = BASE_DIR / "master.json"

RAW.mkdir(parents=True, exist_ok=True)
PARSED.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# Manual URLs from .env (comma-separated) — ALWAYS fetched & saved
# .env example:
# CRAWL_MANUAL_URLS=https://site/page#frag1, https://site/page#frag2
# ──────────────────────────────────────────────────────────────────────────────
def env_manual_urls():
    raw = os.getenv("CRAWL_MANUAL_URLS", "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]

MANUAL_URLS = env_manual_urls()

# ──────────────────────────────────────────────────────────────────────────────
# Case-study rules (special case) — kept exactly as your original
# ──────────────────────────────────────────────────────────────────────────────
CASE_STUDY_INDEX  = "https://www.incede.ai/resources/case-studies"
CASE_STUDY_PREFIX = "https://www.incede.ai/resources/"

def _norm(u: str) -> str:
    if not u:
        return ""
    u = u.split("#", 1)[0].split("?", 1)[0]
    return u.rstrip("/")

def is_case_study_detail(u: str) -> bool:
    u = _norm(u)
    return u.startswith(CASE_STUDY_PREFIX.rstrip("/")) and u != _norm(CASE_STUDY_INDEX)

def filter_links(current_url: str, links: list[str]) -> list[str]:
    """Return the list of links we are willing to enqueue.

    Rules:
      • If we are on the case-studies index page → do not expand any links.
      • Else, drop any individual case-study detail URLs.
    """
    cur = _norm(current_url)
    if cur == _norm(CASE_STUDY_INDEX):
        return []
    out = []
    for u in links:
        if is_case_study_detail(u):
            continue
        out.append(u)
    return out

# ──────────────────────────────────────────────────────────────────────────────
# URL helpers & parsing
# ──────────────────────────────────────────────────────────────────────────────
SKIP_EXT = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".mp4", ".mp3", ".wav", ".zip", ".rar", ".7z", ".gz", ".css", ".js",
    ".json", ".xml", ".txt", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx"
}

def slug(url: str) -> str:
    host = re.sub(r"^https?://", "", url).split("/")[0]
    return f"{host}_{hashlib.md5(url.encode()).hexdigest()[:10]}"

def same_host(a: str, b: str) -> bool:
    return urllib.parse.urlparse(a).netloc == urllib.parse.urlparse(b).netloc

def norm_link(href: str, base: str):
    if not href:
        return None
    href = href.strip()
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    absu = urllib.parse.urljoin(base, href)
    u = urllib.parse.urlparse(absu)
    if u.scheme not in ("http", "https"):
        return None
    if any(u.path.lower().endswith(ext) for ext in SKIP_EXT):
        return None
    return urllib.parse.urlunparse(u)

def _section_text_by_fragment(soup: BeautifulSoup, frag: str) -> str | None:
    """Return text of the section that corresponds to the given fragment id."""
    if not frag:
        return None
    node = soup.find(id=frag)
    if not node:
        return None
    # climb to a reasonable container
    container = node
    while container and container.name not in ("section", "article", "div", "main"):
        container = container.parent
    section = container or node
    # Prefer stopping at the next sibling section-like block if huge
    text = " ".join(section.get_text(" ").split())
    return text.strip() or None

def parse(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()

    # Split base for links vs fragment scoping
    frag = None
    base_for_links = base_url
    if "#" in base_url:
        base_for_links, frag = base_url.split("#", 1)

    # Title
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")

    # Anchor-scoped extraction if fragment present
    if frag:
        section_text = _section_text_by_fragment(soup, frag)
        if section_text:
            text = section_text
        else:
            # fallback to full page if id not found
            text = " ".join(soup.get_text(" ").split())
    else:
        text = " ".join(soup.get_text(" ").split())

    # Links (resolve against base page URL, not fragment)
    links = []
    for a in soup.find_all("a", href=True):
        n = norm_link(a["href"], base_for_links)
        if n:
            links.append(n)
    return title, text, links

async def fetch(page, url: str) -> str:
    await page.goto(url, wait_until="networkidle", timeout=60000)
    return await page.content()

def save_item(url: str, html: str, title: str, text: str, links: list[str]):
    name = slug(url)
    (RAW / f"{name}.html").write_text(html, encoding="utf-8")
    item = {
        "id": name,
        "url": url,
        "title": title,
        "timestamp": int(time.time()),
        "text": text,
        "links": links,  # stored links are the filtered, crawlable ones
    }
    (PARSED / f"{name}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return item

def rebuild_master():
    items = []
    for p in PARSED.glob("*.json"):
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except:
            pass
    MASTER.write_text(json.dumps({"count": len(items), "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")

# ──────────────────────────────────────────────────────────────────────────────
# Force-fetch manual URLs (ignores max_pages and dedup)
# ──────────────────────────────────────────────────────────────────────────────
async def fetch_and_save_manual(start_url: str, page) -> int:
    count = 0
    for url in MANUAL_URLS:
        if not same_host(start_url, url):
            continue
        try:
            html = await fetch(page, url)
            title, text, _ = parse(html, url)  # anchor-scoped if hash present
            # Save without queued links to avoid SPA explosion
            save_item(url, html, title, text, links=[])
            count += 1
            print(f"[manual] saved {url}")
        except Exception as e:
            print(f"[manual ERR] {url}: {e}")
    return count

# ──────────────────────────────────────────────────────────────────────────────
# Crawler (BFS)
# ──────────────────────────────────────────────────────────────────────────────
async def crawl(start_url: str, max_depth: int, max_pages: int):
    seen = set()
    q = deque([(start_url, 0)])
    crawled = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        try:
            # 1) Always fetch manual URLs first (don’t count toward max_pages)
            await fetch_and_save_manual(start_url, page)

            # 2) Then normal crawl within limits
            while q and crawled < max_pages:
                url, d = q.popleft()
                key = url.split("#", 1)[0]
                if key in seen or not same_host(start_url, url):
                    continue
                seen.add(key)
                try:
                    html = await fetch(page, url)
                    title, text, links = parse(html, url)
                    links = filter_links(url, links)
                    save_item(url, html, title, text, links)
                    crawled += 1
                    print(f"[{crawled}/{max_pages}] {url} (depth={d}, links={len(links)})")
                    if d < max_depth:
                        for ln in links:
                            k = ln.split("#", 1)[0]
                            if k not in seen:
                                q.append((ln, d + 1))
                except Exception as e:
                    print(f"[ERR] {url}: {e}")
        finally:
            await ctx.close()
            await browser.close()

    rebuild_master()
    print(f"Done. Crawled {crawled} pages. Manual saved: {len(MANUAL_URLS)}")

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python crawl.py <START_URL> <MAX_DEPTH:int> <MAX_PAGES:int> [RUN_ID]")
        sys.exit(1)
    asyncio.run(crawl(sys.argv[1], int(sys.argv[2]), int(sys.argv[3])))