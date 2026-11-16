#!/usr/bin/env python3
"""Extra sweep: role+Oslo queries and deeper pagination for high-yield keywords."""
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
        time.sleep(1.2*i+1)
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

ROLE_Q = [
 "bank Oslo","financial services Oslo","sales Oslo","customer service Oslo",
 "marketing Oslo","administration Oslo","kundeservice Oslo","salg Oslo",
 "account manager Oslo","customer advisor Oslo","business development Oslo",
 "financial analyst Oslo","credit analyst Oslo","KYC Oslo","AML Oslo",
 "payment Oslo","treasury Oslo","relationship manager Oslo","digital marketing Oslo",
 "content marketing Oslo","social media manager Oslo","sales advisor Oslo",
 "customer success Oslo","accountant Oslo","financial controller Oslo",
 "inside sales Oslo","business development manager Oslo","growth marketing Oslo",
 "account executive Oslo","kundemedarbeider Oslo","rådgiver finans Oslo",
 "økonomi Oslo","kontor og administrasjon Oslo","bank finans forsikring Oslo",
 "salg kundeservice Oslo","financial services","fintech Oslo","insurance Oslo",
 "pharma sales Oslo","retail sales Oslo","marketing manager Oslo","brand manager Oslo",
 "commercial manager Oslo","senior advisor Oslo","graduate Oslo","trainee Oslo",
]
DEEP = ["bank","sales","kundeservice","financial services","marketing","English","engelsk",
        "administration","account manager","business development","customer advisor"]

def build_urls():
    urls = []
    for q in ROLE_Q:
        for pg in (1,2):
            urls.append(f"https://www.finn.no/job/search?q={urllib.parse.quote(q)}" + (f"&page={pg}" if pg>1 else ""))
    for q in DEEP:
        for pg in range(1,13):
            urls.append(f"https://www.finn.no/job/search?q={urllib.parse.quote(q)}" + (f"&page={pg}" if pg>1 else ""))
    return urls

def main():
    path = f"{WORKDIR}/finn_cards.json"
    cards = {c["id"]: c for c in json.load(open(path))}
    before = len(cards)
    urls = build_urls()
    new_cards = {}
    def job(u):
        return u, parse_cards(fetch(u))
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i,(u,got) in enumerate(ex.map(job, urls)):
            for c in got:
                if c["id"] not in cards and c["id"] not in new_cards:
                    c["src_q"] = urllib.parse.unquote(u.split("q=")[1].split("&")[0])
                    new_cards[c["id"]] = c
            if (i+1) % 30 == 0: print(f"{i+1}/{len(urls)} new={len(new_cards)}", flush=True)
    for cid,c in new_cards.items(): cards[cid]=c
    json.dump(list(cards.values()), open(path,"w"), ensure_ascii=False, indent=1)
    oslo_new = [c for c in new_cards.values() if re.search(r"\bOslo\b", c["location"], re.I)]
    print(f"before={before} after={len(cards)} new={len(new_cards)} new_oslo={len(oslo_new)}")

if __name__ == "__main__":
    main()
