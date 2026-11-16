#!/usr/bin/env python3
"""SSR harvest of arbeidsplassen.nav.no search pages. Extracts result cards for multiple queries."""
import re, html, json, time, sys, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE = "https://arbeidsplassen.nav.no/stillinger"

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def parse_cards(raw):
    treff = None
    m = re.search(r'>([\d\s\u00a0]+)<[^>]*>?\s*treff|([\d\s\u00a0]+)\s*treff', raw)
    m2 = re.search(r'(\d[\d\s\u00a0]*)\s*treff', raw)
    if m2:
        treff = int(m2.group(1).replace(" ", "").replace("\u00a0", ""))
    cards = []
    chunks = raw.split('<h2 class="overflow-wrap-anywhere')
    for ch in chunks[1:]:
        href = re.search(r'href="(/stillinger/stilling/[a-f0-9-]{36})"', ch)
        title = re.search(r'href="/stillinger/stilling/[a-f0-9-]{36}">([^<]+)</a>', ch)
        if not href or not title:
            continue
        jt = re.search(r'</h2></div><p class="overflow-wrap-anywhere aksel-body-short aksel-body-short--medium">([^<]+)', ch)
        emp = re.search(r'visually-hidden">Arbeidsgiver</p></div><p class="overflow-wrap-anywhere aksel-body-short aksel-body-short--medium">([^<]+)', ch)
        loc = re.search(r'visually-hidden">Sted</p></div><p class="overflow-wrap-anywhere aksel-body-short aksel-body-short--medium">([^<]+)', ch)
        dl = re.search(r'Søk senest ([^<]+)<', ch)
        snap = "Superrask søknad" in ch
        remote = re.search(r'Justerbar|Hjemmekontor', ch)
        cards.append({
            "uuid": href.group(1).rsplit("/", 1)[1],
            "href": href.group(1),
            "title": html.unescape(title.group(1)).strip(),
            "jobtitle": html.unescape(jt.group(1)).strip() if jt else "",
            "employer": html.unescape(emp.group(1)).strip() if emp else "",
            "location": html.unescape(loc.group(1)).strip() if loc else "",
            "deadline": html.unescape(dl.group(1)).strip() if dl else "",
            "snap": snap,
        })
    return treff, cards

QUERIES = [
    ("bank", "q=bank&county=OSLO"),
    ("banking", "q=banking&county=OSLO"),
    ("finance", "q=finance&county=OSLO"),
    ("financial", "q=financial&county=OSLO"),
    ("customer service", "q=customer%20service&county=OSLO"),
    ("customer support", "q=customer%20support&county=OSLO"),
    ("customer success", "q=customer%20success&county=OSLO"),
    ("kundeservice", "q=kundeservice&county=OSLO"),
    ("sales", "q=sales&county=OSLO"),
    ("marketing", "q=marketing&county=OSLO"),
    ("english", "q=english&county=OSLO"),
    ("international", "international=true&county=OSLO"),
    ("kontor+intl", "international=true&occupationFirstLevels=Kontor%20og%20%C3%B8konomi"),
    ("salg+intl", "international=true&occupationFirstLevels=Salg%20og%20service"),
    ("it+intl", "international=true&occupationFirstLevels=IT"),
]

all_cards = {}
log = []
for name, qs in QUERIES:
    url = f"{BASE}?{qs}&v=6"
    for attempt in range(3):
        try:
            raw = fetch(url)
            break
        except Exception as e:
            print("ERR", name, e, flush=True)
            time.sleep(8)
    else:
        continue
    treff, cards = parse_cards(raw)
    log.append(f"{name}: treff={treff} cards={len(cards)}")
    print(name, "treff:", treff, "cards:", len(cards), flush=True)
    for c in cards:
        u = c["uuid"]
        if u not in all_cards:
            c["q"] = name
            all_cards[u] = c
    time.sleep(2.5)

with open("/home/ubuntu/nav_ssr_hits.json", "w") as f:
    json.dump(list(all_cards.values()), f, ensure_ascii=False)
print("SAVED", len(all_cards), "unique")
print("\n".join(log))
