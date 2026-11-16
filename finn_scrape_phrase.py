#!/usr/bin/env python3
"""Extra sweep using English-language phrases as queries to catch missed English ads."""
import json, re, subprocess, sys, time, html, urllib.parse, os
from concurrent.futures import ThreadPoolExecutor
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")

def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}",url],
                               capture_output=True,text=True,timeout=60)
            if len(r.stdout) > 50000: return r.stdout
        except Exception: pass
        time.sleep(1.2*i+1)
    return ""

def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I); s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>","\n",s,flags=re.I); s = TAG_RE.sub(" ",s); s = html.unescape(s)
    return "\n".join(l for l in (WS_RE.sub(" ",x).strip() for x in s.split("\n")) if l)

def parse_cards(page):
    out = []
    for m in re.finditer(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"(.*?)</article>', page, re.S):
        aid, blob = m.group(1), m.group(2)
        tm = re.search(r'<a[^>]*class="[^"]*job-card-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blob, re.S)
        if not tm: continue
        cm = re.search(r"<strong[^>]*>(.*?)</strong>", blob, re.S)
        lm = re.search(r'class="[^"]*truncate[^"]*"[^>]*>(.*?)</span>', blob, re.S)
        dm = re.search(r'dateTime="([^"]+)"', blob)
        out.append({"id": aid, "title": WS_RE.sub(" ", strip_tags(tm.group(2))).strip(),
                    "company": WS_RE.sub(" ", strip_tags(cm.group(1))).strip() if cm else "",
                    "location": WS_RE.sub(" ", strip_tags(lm.group(1))).strip() if lm else "",
                    "date": dm.group(1) if dm else "", "url": f"https://www.finn.no/job/ad/{aid}"})
    return out

QUERIES = ["English speaking", "fluent in English", "English working language",
           "working language is English", "English language skills", "written and spoken English",
           "English speaking sales", "English speaking customer service", "English speaking bank"]

def main():
    path = f"{WORKDIR}/finn_cards.json"
    cards = {c["id"]: c for c in json.load(open(path))}
    before = len(cards)
    urls = []
    for q in QUERIES:
        for pg in (1, 2, 3):
            urls.append(f"https://www.finn.no/job/search?q={urllib.parse.quote(q)}" + (f"&page={pg}" if pg > 1 else ""))
    new = {}
    def job(u):
        return u, parse_cards(fetch(u))
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i, (u, got) in enumerate(ex.map(job, urls)):
            for c in got:
                if c["id"] not in cards and c["id"] not in new:
                    new[c["id"]] = c
            if (i+1) % 10 == 0: print(f"{i+1}/{len(urls)} new={len(new)}", flush=True)
    for cid, c in new.items(): cards[cid] = c
    json.dump(list(cards.values()), open(path, "w"), ensure_ascii=False, indent=1)
    oslo_new = [c for c in new.values() if re.search(r"\bOslo\b", c["location"], re.I)]
    print(f"before={before} after={len(cards)} new={len(new)} new_oslo={len(oslo_new)}")
    json.dump(oslo_new, open(f"{WORKDIR}/finn_phrase_new_oslo.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
