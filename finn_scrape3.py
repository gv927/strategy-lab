#!/usr/bin/env python3
"""Robust finn sweep: retries, more pages, tracks total result counts."""
import json, re, subprocess, sys, time, html, urllib.parse, os

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")

def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(["curl", "-sL", "--max-time", "45", "-H", f"User-Agent: {UA}",
                                "-H", "Accept-Language: en-US,en;q=0.9,nb;q=0.8", url],
                               capture_output=True, text=True, timeout=60)
            if len(r.stdout) > 50000:
                return r.stdout
        except Exception:
            pass
        time.sleep(2 + 2*i)
    return ""

def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I); s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>","\n",s,flags=re.I); s = TAG_RE.sub(" ",s); s = html.unescape(s)
    return "\n".join(WS_RE.sub(" ",l).strip() for l in s.split("\n") if WS_RE.sub(" ",l).strip())

def parse_cards(page):
    out = []
    for m in re.finditer(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"(.*?)</article>', page, re.S):
        aid, blob = m.group(1), m.group(2)
        tm = re.search(r'<a[^>]*class="[^"]*job-card-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blob, re.S)
        if not tm:
            continue
        title = WS_RE.sub(" ", strip_tags(tm.group(2))).strip()
        cm = re.search(r"<strong[^>]*>(.*?)</strong>", blob, re.S)
        comp = WS_RE.sub(" ", strip_tags(cm.group(1))).strip() if cm else ""
        lm = re.search(r'class="[^"]*truncate[^"]*"[^>]*>(.*?)</span>', blob, re.S)
        loc = WS_RE.sub(" ", strip_tags(lm.group(1))).strip() if lm else ""
        dm = re.search(r'dateTime="([^"]+)"', blob)
        out.append({"id": aid, "title": title, "company": comp, "location": loc,
                    "date": dm.group(1) if dm else "", "url": f"https://www.finn.no/job/ad/{aid}"})
    return out

KEYWORDS = [
    "bank","banking","financial services","finance","customer service","kundeservice",
    "customer support","sales","salg","marketing","digital marketing","administration",
    "administrasjon","account manager","customer advisor","kunderådgiver","service advisor",
    "salgskonsulent","financial advisor","risk","compliance","treasury","wealth management",
    "insurance","broker","investment","loan officer","business development","marketing manager",
    "business analyst","inside sales","accountant","økonom","kontor","sales advisor",
    "kundeseier","kundeservice consultant","backoffice","operations","product marketing",
]

def main():
    path = f"{WORKDIR}/finn_cards.json"
    cards = {c["id"]: c for c in json.load(open(path))}
    before = len(cards)
    counts = {}
    for kw in KEYWORDS:
        tot = None
        for pg in range(1, 5):
            url = f"https://www.finn.no/job/search?q={urllib.parse.quote(kw)}" + (f"&page={pg}" if pg>1 else "")
            page = fetch(url)
            got = parse_cards(page)
            if tot is None:
                tm = re.search(r'class="sr-only">(\d+)\s*resultater', page)
                tot = int(tm.group(1)) if tm else None
            if not got:
                print(f"kw={kw} p={pg} EMPTY", file=sys.stderr); continue
            for c in got:
                c["keyword"] = kw
                if c["id"] not in cards:
                    cards[c["id"]] = c
            time.sleep(0.3)
        counts[kw] = tot
        print(f"kw={kw} total_results={tot} cards_so_far={len(cards)}", file=sys.stderr)
    json.dump(list(cards.values()), open(path,"w"), ensure_ascii=False, indent=1)
    json.dump(counts, open(f"{WORKDIR}/finn_kw_counts.json","w"), indent=1)
    print(f"before={before} after={len(cards)}")

if __name__ == "__main__":
    main()
