#!/usr/bin/env python3
"""Fetch finn detail pages for ALL Oslo cards (threaded), cache to disk."""
import json, os, re, subprocess, sys, time, html
from concurrent.futures import ThreadPoolExecutor

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
CACHE = f"{WORKDIR}/finn_detail_cache"
os.makedirs(CACHE, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")

def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>","\n",s,flags=re.I)
    s = TAG_RE.sub(" ",s); s = html.unescape(s)
    lines = [WS_RE.sub(" ",l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(["curl","-sL","--max-time","40","-H",f"User-Agent: {UA}",
                                "-H","Accept-Language: en-US,en;q=0.9,nb;q=0.8",url],
                               capture_output=True,text=True,timeout=55)
            if len(r.stdout) > 20000:
                return r.stdout
        except Exception:
            pass
        time.sleep(1.5*i+1)
    return ""

def parse_detail(page, card):
    body_m = re.search(r'<section[^>]*aria-labelledby="ad-summary-heading".*?</section>', page, re.S)
    blob = page
    if body_m:
        blob = body_m.group(0)
    # full body: from ad body heading to end of ad-content section
    m = re.search(r'id="ad-body"', page)
    if m:
        blob = page[m.start():]
    blob = re.split(r"Lignende annonser|Andre jobber|Similar ads", blob)[0]
    body = strip_tags(blob)
    # header block (title, company, key info)
    head = page[:m.start()] if m else page[:0]
    info = {}
    for mm in re.finditer(r'<li class="flex flex-col"><span[^>]*>(.*?)</span>\s*<strong class="key-info-text">(.*?)</strong></li>', head, re.S):
        k = WS_RE.sub(" ", strip_tags(mm.group(1))).strip()
        v = WS_RE.sub(" ", strip_tags(mm.group(2))).strip()
        if k: info[k] = v
    for mm in re.finditer(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', head, re.S):
        k = WS_RE.sub(" ", strip_tags(mm.group(1))).strip()
        v = WS_RE.sub(" ", strip_tags(mm.group(2))).strip()
        if k: info.setdefault(k,v)
    ttl = re.search(r'<h1[^>]*>(.*?)</h1>', page, re.S)
    title = WS_RE.sub(" ", strip_tags(ttl.group(1))).strip() if ttl else card["title"]
    return {**card, "title": title, "body": body, "info": info, "body_len": len(body),
            "http_ok": len(page) > 20000}

def worker(card):
    aid = card["id"]
    path = f"{CACHE}/{aid}.json"
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            pass
    page = fetch(card["url"])
    d = parse_detail(page, card)
    json.dump(d, open(path,"w"), ensure_ascii=False)
    return d

def main():
    cards = json.load(open(f"{WORKDIR}/finn_cards.json"))
    oslo = [c for c in cards if re.search(r"\bOslo\b", c["location"], re.I)]
    print("oslo cards:", len(oslo))
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for d in ex.map(worker, oslo):
            done += 1
            if done % 50 == 0:
                print("done", done, flush=True)
    print("finished", done)

if __name__ == "__main__":
    main()
