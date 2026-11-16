#!/usr/bin/env python3
"""Sweep finn for 'English'/'engelsk' mentions, many pages, keep Oslo cards."""
import json, re, subprocess, sys, time, html, urllib.parse, os
from concurrent.futures import ThreadPoolExecutor

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")

def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}",
                                "-H","Accept-Language: en-US,en;q=0.9,nb;q=0.8",url],
                               capture_output=True,text=True,timeout=60)
            if len(r.stdout) > 50000: return r.stdout
        except Exception: pass
        time.sleep(1.5*i+1)
    return ""

def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I); s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>","\n",s,flags=re.I); s = TAG_RE.sub(" ",s); s = html.unescape(s)
    lines = [WS_RE.sub(" ",l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def parse_cards(page):
    out = []
    for m in re.finditer(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"(.*?)</article>', page, re.S):
        aid, blob = m.group(1), m.group(2)
        tm = re.search(r'<a[^>]*class="[^"]*job-card-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blob, re.S)
        if not tm: continue
        title = WS_RE.sub(" ", strip_tags(tm.group(2))).strip()
        cm = re.search(r"<strong[^>]*>(.*?)</strong>", blob, re.S)
        comp = WS_RE.sub(" ", strip_tags(cm.group(1))).strip() if cm else ""
        lm = re.search(r'class="[^"]*truncate[^"]*"[^>]*>(.*?)</span>', blob, re.S)
        loc = WS_RE.sub(" ", strip_tags(lm.group(1))).strip() if lm else ""
        dm = re.search(r'dateTime="([^"]+)"', blob)
        out.append({"id":aid,"title":title,"company":comp,"location":loc,
                    "date": dm.group(1) if dm else "","url":f"https://www.finn.no/job/ad/{aid}"})
    return out

def job(url):
    page = fetch(url)
    return parse_cards(page)

def main():
    path = f"{WORKDIR}/finn_cards.json"
    cards = {c["id"]: c for c in json.load(open(path))}
    before = len(cards)
    urls = []
    for kw in ["English", "engelsk"]:
        for pg in range(1, 31):
            urls.append(f"https://www.finn.no/job/search?q={urllib.parse.quote(kw)}" + (f"&page={pg}" if pg>1 else ""))
    # dedupe pages
    seen_pages = set()
    new_cards = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i, got in enumerate(ex.map(job, urls)):
            for c in got:
                if c["id"] not in cards and c["id"] not in new_cards:
                    new_cards[c["id"]] = c
            print(f"page {i+1}/{len(urls)} new={len(new_cards)}", flush=True)
    for cid, c in new_cards.items():
        cards[cid] = c
    json.dump(list(cards.values()), open(path,"w"), ensure_ascii=False, indent=1)
    oslo_new = [c for c in new_cards.values() if re.search(r"\bOslo\b", c["location"], re.I)]
    print(f"before={before} after={len(cards)} new={len(new_cards)} new_oslo={len(oslo_new)}")

if __name__ == "__main__":
    main()
