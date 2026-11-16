#!/usr/bin/env python3
"""Parse SSR search page HTML: extract result cards (title, employer, location, href/uuid, summary)."""
import re, html, json, sys, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def visible_text(raw):
    raw2 = re.sub(r"<script[\s\S]*?</script>", " ", raw)
    raw2 = re.sub(r"<style[\s\S]*?</style>", " ", raw2)
    t = re.sub(r"<[^>]+>", "\n", raw2)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://arbeidsplassen.nav.no/stillinger?q=bank&county=OSLO&v=6"
    raw = fetch(url)
    print("HTML len:", len(raw))
    text = visible_text(raw)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # print the segment around first result link
    start = None
    for i, l in enumerate(lines):
        if re.search(r"[Tt]reff", l):
            print("TREFF LINE:", l)
    # find results section
    try:
        idx = text.find("Sorter etter")
        print(text[idx:idx+3000])
    except Exception as e:
        print(e)
