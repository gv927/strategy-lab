#!/usr/bin/env python3
"""Parse SSR search results: extract ad cards with href/uuid, title, employer, location, summary; also pagination."""
import re, html, sys, urllib.request, urllib.parse

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

def parse(url):
    raw = fetch(url)
    # find all ad links
    links = re.findall(r'href="(/stillinger/stilling/[a-f0-9-]{36})"', raw)
    # find the treff count
    m = re.search(r'(\d[\d\s\u00a0]*)\s*treff', raw)
    text = visible_text(raw)
    # results section starts after "Sorter etter" ... let's find markers: lines after 'Neste' or the first card
    # Each card: link, then title, "Arbeidsgiver", employer, "Sted", location...
    seg = text
    # locate first occurrence of "Søknadsfrist" sort options area end: use marker 'Vis alle' then skip; find start via first uuid title
    cards = []
    # split text by uuid links: find positions of titles is hard; use regex on raw HTML instead
    # Card pattern in raw HTML: <a href="/stillinger/stilling/UUID" ... then title in a heading (h2/h3?) 
    card_re = re.findall(r'href="(/stillinger/stilling/[a-f0-9-]{36})"[\s\S]{0,2000}?<(h\d)[^>]*>([\s\S]*?)</\2>', raw)
    for href, tag, inner in card_re:
        title = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        cards.append({"href": href, "title": title})
    return m.group(0) if m else "?", links, cards, text

if __name__ == "__main__":
    url = sys.argv[1]
    treff, links, cards, text = parse(url)
    print("TREFF:", treff)
    print("LINKS:", len(links))
    for c in cards[:30]:
        print("-", c["title"][:100], "|", c["href"])
