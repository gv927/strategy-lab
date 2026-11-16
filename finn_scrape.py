#!/usr/bin/env python3
"""Scrape finn.no job search SSR HTML for Oslo listings matching keywords."""
import json, re, subprocess, sys, time, html

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"

KEYWORDS = [
    "bank", "banking", "customer service", "sales", "marketing",
    "administration", "financial services", "advisor", "account manager",
    "kundeservice", "salg", "administrasjon", "bank", "finance",
    "digital marketing", "customer support", "service advisor", "kontor",
    "økonomi", "sales advisor", "relationship manager", "financial",
]

def fetch(url):
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "45", "-H", f"User-Agent: {UA}",
             "-H", "Accept-Language: en-US,en;q=0.9,nb;q=0.8", url],
            capture_output=True, text=True, timeout=60)
        return r.stdout
    except Exception as e:
        print("ERR", url, e, file=sys.stderr)
        return ""

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

def strip_tags(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", s, flags=re.I)
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    lines = [WS_RE.sub(" ", l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def parse_cards(page):
    """Extract job cards from finn SSR HTML."""
    out = []
    # each card: <article class="... job-card-article__list" id="NNN"> ... job-card-link ... </article>
    for m in re.finditer(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"(.*?)</article>', page, re.S):
        aid, blob = m.group(1), m.group(2)
        tm = re.search(r'<a[^>]*class="[^"]*job-card-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blob, re.S)
        if not tm:
            continue
        href = html.unescape(tm.group(1))
        title = WS_RE.sub(" ", strip_tags(tm.group(2))).strip()
        # company: <strong ...>company</strong>
        comp = ""
        cm = re.search(r"<strong[^>]*>(.*?)</strong>", blob, re.S)
        if cm:
            comp = WS_RE.sub(" ", strip_tags(cm.group(1))).strip()
        # location pill
        loc = ""
        lm = re.search(r'class="[^"]*truncate[^"]*"[^>]*>(.*?)</span>', blob, re.S)
        if lm:
            loc = WS_RE.sub(" ", strip_tags(lm.group(1))).strip()
        dm = re.search(r'dateTime="([^"]+)"', blob)
        date = dm.group(1) if dm else ""
        out.append({"id": aid, "title": title, "company": comp, "location": loc,
                    "date": date, "url": f"https://www.finn.no/job/ad/{aid}"})
    return out

def main():
    cards = {}
    for kw in KEYWORDS:
        for page in (1, 2):
            url = f"https://www.finn.no/job/search?q={quote(kw)}" + (f"&page={page}" if page > 1 else "")
            htmltext = fetch(url)
            got = parse_cards(htmltext)
            print(f"kw={kw} page={page} cards={len(got)} bytes={len(htmltext)}", file=sys.stderr)
            for c in got:
                c["keyword"] = kw
                if c["id"] not in cards:
                    cards[c["id"]] = c
                else:
                    cards[c["id"]].setdefault("kw_all", [])
                    if kw not in cards[c["id"]]["kw_all"]:
                        cards[c["id"]]["kw_all"].append(kw)
            time.sleep(0.6)
    with open(f"{WORKDIR}/finn_cards.json", "w") as f:
        json.dump(list(cards.values()), f, ensure_ascii=False, indent=1)
    print(f"TOTAL unique cards: {len(cards)}")

def quote(s):
    import urllib.parse
    return urllib.parse.quote(s)

if __name__ == "__main__":
    main()
