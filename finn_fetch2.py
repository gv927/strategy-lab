#!/usr/bin/env python3
"""Fetch raw finn detail HTML for all Oslo cards; parse body + key info correctly."""
import json, os, re, subprocess, sys, time, html
from concurrent.futures import ThreadPoolExecutor

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
RAWC = f"{WORKDIR}/finn_detail_html"
os.makedirs(RAWC, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")

def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>","\n",s,flags=re.I)
    s = TAG_RE.sub(" ",s); s = html.unescape(s)
    lines = [WS_RE.sub(" ",l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def fetch(url, tries=3):
    for i in range(tries):
        try:
            r = subprocess.run(["curl","-sL","--max-time","40","-H",f"User-Agent: {UA}",
                                "-H","Accept-Language: en-US,en;q=0.9,nb;q=0.8",url],
                               capture_output=True,text=True,timeout=55)
            if len(r.stdout) > 20000: return r.stdout
        except Exception: pass
        time.sleep(1.2*i+1)
    return ""

def get_html(card):
    aid = card["id"]
    path = f"{RAWC}/{aid}.html"
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return open(path, encoding="utf-8", errors="replace").read()
    p = fetch(card["url"])
    if p:
        open(path,"w",encoding="utf-8",errors="replace").write(p)
    return p

def parse(page, card):
    body_parts = []
    # 1) short summary content (Kortversjonen)
    m = re.search(r'id="ad-summary-content"(.*?)</section>\s*</section>', page, re.S)
    if m:
        body_parts.append(strip_tags(m.group(1)))
    # 2) full ad body: section starting with <h1 class="t3 mb-16">
    i = page.find('<h1 class="t3 mb-16">')
    if i == -1:
        i = page.find('<h1')
    j = page.find('id="recommendations-heading"')
    if i != -1:
        end = j if j > i else len(page)
        seg = page[i:end]
        seg = re.split(r'<h2[^>]*>\s*Om arbeidsgiveren', seg)[0]
        body_parts.append(strip_tags(seg))
    body = "\n".join(body_parts)
    # key info from header block
    head_end = i if i != -1 else len(page)
    head = page[:head_end]
    info = {}
    for mm in re.finditer(r'<li class="flex flex-col">\s*<span[^>]*>(.*?)</span>\s*<strong class="key-info-text">(.*?)</strong></li>', head, re.S):
        k = WS_RE.sub(" ", strip_tags(mm.group(1))).strip()
        v = WS_RE.sub(" ", strip_tags(mm.group(2))).strip()
        if k: info[k] = v
    ttl = re.search(r'<h1[^>]*>(.*?)</h1>', page, re.S)
    title = WS_RE.sub(" ", strip_tags(ttl.group(1))).strip() if ttl else card["title"]
    comp = ""
    cm = re.search(r'<h2[^>]*class="t2 md:t1[^"]*"[^>]*>(.*?)</h2>', page, re.S)
    if cm: comp = WS_RE.sub(" ", strip_tags(cm.group(1))).strip()
    return {**card, "title": title, "header_title": comp, "body": body, "info": info,
            "body_len": len(body), "html_ok": len(page) > 20000}

def main():
    cards = json.load(open(f"{WORKDIR}/finn_cards.json"))
    oslo = [c for c in cards if re.search(r"\bOslo\b", c["location"], re.I)]
    print("oslo cards:", len(oslo), flush=True)
    out = []
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for c, page in zip(oslo, ex.map(lambda cc: get_html(cc), oslo)):
            out.append(parse(page, c))
            done += 1
            if done % 100 == 0: print("parsed", done, flush=True)
    json.dump(out, open(f"{WORKDIR}/finn_details_all.json","w"), ensure_ascii=False, indent=1)
    ok = sum(1 for d in out if d["html_ok"])
    print("parsed", len(out), "html_ok", ok, "empty_body", sum(1 for d in out if d["body_len"] < 200))

if __name__ == "__main__":
    main()
