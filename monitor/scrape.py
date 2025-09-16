import json, time, re, yaml
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from extractors import extract_items_from_html
from diff import compute_diff

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WEB_DIR  = ROOT / "web"

HEADERS = {"User-Agent": "itau-beneficios-monitor/1.0 (+github actions; contact: n/a)"}

def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def allowed(url, allow_patterns):
    return any(re.search(p, url) for p in allow_patterns)

def crawl(seed_urls, allow_patterns, max_depth=2, max_pages=50):
    seen, q, pages = set(), list(seed_urls), []
    depth = {u:0 for u in q}
    while q and len(pages) < max_pages:
        url = q.pop(0)
        if url in seen: continue
        seen.add(url)
        try:
            html = fetch(url)
        except Exception:
            continue
        pages.append((url, html))
        if depth[url] < max_depth:
            soup = BeautifulSoup(html, "lxml")
            for a in soup.select("a[href]"):
                href = a.get("href").strip()
                if href.startswith("#") or href.startswith("mailto:"): continue
                if href.startswith("/"):
                    href = urljoin("https://www.itau.com.uy", href)
                if urlparse(href).netloc.endswith("itau.com.uy") and allowed(href, allow_patterns):
                    if href not in seen:
                        q.append(href)
                        depth[href] = depth[url] + 1
        time.sleep(0.5)
    return pages

def main():
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    WEB_DIR.mkdir(exist_ok=True, parents=True)

    cfg = yaml.safe_load((ROOT / "monitor" / "sites.yaml").read_text(encoding="utf-8"))
    pages = crawl(cfg["seed_urls"], cfg["allow_patterns"], cfg.get("max_depth",2), cfg.get("max_pages",50))

    items = []
    for url, html in pages:
        items.extend(extract_items_from_html(html, url))

    current_path = DATA_DIR / "current.json"
    changelog_path = DATA_DIR / "changelog.json"

    old_items = []
    if current_path.exists():
        old_items = json.loads(current_path.read_text(encoding="utf-8"))

    diff = compute_diff(old_items, items)

    if diff["added"] or diff["removed"] or diff["changed"]:
        current_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        log = []
        if changelog_path.exists():
            log = json.loads(changelog_path.read_text(encoding="utf-8"))
        log.insert(0, diff)
        log = log[:200]
        changelog_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        (WEB_DIR / "changes.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    if not (WEB_DIR / "changes.json").exists():
        (WEB_DIR / "changes.json").write_text("[]", encoding="utf-8")

if __name__ == "__main__":
    main()

