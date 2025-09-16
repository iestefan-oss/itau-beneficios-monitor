import re
from bs4 import BeautifulSoup

# Soportar "25% menos", "15% OFF", "ahorro 20%", etc.
PERCENT_RE = re.compile(r"(?:^|\\b)(\\d{1,2})\\s?%")
VIGENCIA_RE = re.compile(r"(?:vigencia|hasta el)[:\\s]*(.*?)(?:\\.|$)", re.IGNORECASE)

KEYWORDS = ("menos", "descuento", "off", "%", "ahorro")

def normalize_text(s):
    return " ".join(s.split())

def guess_title(block):
    # Buscar un título interno "amigable"
    for sel in ["h1","h2","h3",".title","strong","b"]:
        el = block.select_one(sel)
        if el and el.get_text(strip=True):
            return normalize_text(el.get_text(" ", strip=True))
    return normalize_text(block.get_text(" ", strip=True))[:120]

def guess_percent(text):
    # Aceptar "OFF" sin % explícito (ej: "25 OFF")
    m = PERCENT_RE.search(text.replace("OFF","%").replace("off","%"))
    return int(m.group(1)) if m else None

def guess_vigencia(text):
    m = VIGENCIA_RE.search(text)
    return normalize_text(m.group(1)) if m else None

def extract_items_from_html(html, url):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Ampliamos candidatos: secciones, artículos, divs, lis y párrafos
    candidates = soup.find_all(["section", "article", "div", "li", "p"])

    seen = set()
    for c in candidates:
        txt = normalize_text(c.get_text(" ", strip=True))
        if len(txt) < 40:
            continue
        low = txt.lower()
        if not any(k in low for k in KEYWORDS):
            continue

        # Link principal (si hubiera)
        link_el = c.select_one("a[href]")
        href = (link_el["href"].strip() if link_el else url) or url
        if href.startswith("/"):
            href = "https://www.itau.com.uy" + href

        title = guess_title(c)
        percent = guess_percent(txt)
        vigencia = guess_vigencia(txt)

        key = (title, percent, href)
        if key in seen:
            continue
        seen.add(key)

        items.append({
            "title": title,
            "percent": percent,
            "vigencia": vigencia,
            "page_url": url,
            "offer_url": href,
            "raw": txt[:1000]
        })
    return items
