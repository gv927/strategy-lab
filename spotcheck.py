#!/usr/bin/env python3
"""READ-ONLY spot-check of LinkedIn guest job view pages: language + Norwegian-requirement analysis."""
import urllib.request, urllib.error, re, html, json, time, sys

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

def fetch(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tries - 1:
                time.sleep(10 * (i + 1)); continue
            return None
        except Exception:
            if i < tries - 1:
                time.sleep(4); continue
            return None
    return None

def get_desc(page):
    if not page:
        return None, {}
    meta = {}
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if m:
        try:
            ld = json.loads(html.unescape(m.group(1)))
            d = ld.get("description", "")
            meta["ld_title"] = ld.get("title", "")
            meta["posted"] = ld.get("datePosted", "")
            meta["valid_through"] = ld.get("validThrough", "")
            loc = ld.get("jobLocation", {})
            if isinstance(loc, list): loc = loc[0] if loc else {}
            addr = (loc or {}).get("address", {})
            meta["city"] = addr.get("addressLocality", "")
            if d:
                return d, meta
        except Exception:
            pass
    m2 = re.search(r'<div class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', page, re.S)
    if m2:
        return m2.group(1), meta
    return None, meta

def strip_html(s):
    s = html.unescape(s)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'</(p|li|div|ul|h[1-6])>', '\n', s, flags=re.I)
    s = re.sub(r'<li[^>]*>', '- ', s, flags=re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'&nbsp;', ' ', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n\s*\n+', '\n', s)
    return s.strip()

CANDIDATES = [
    ("Customer Support Specialist", "Euronext"),
    ("Customer Service Coordinator", "3stepIT"),
    ("Sales Development Representative", "Two"),
    ("Sales Coordinator", "EF"),
    ("Support Agent - Team Lead- Oslo", "Telavox"),
    ("Technical Customer Service Specialist", "Eaton"),
    ("Air Logistics Customer Care Specialist Aerospace", "Kuehne+Nagel"),
    ("Global Digital Marketing Manager", "DNV"),
    ("Growth & Digital Operations Specialist (Graduate)", "Noteless"),
    ("Growth Manager", "VISOID"),
    ("Business Developer (Oslo)", "BrightAnalytics"),
    ("Business Manager", "BNP Paribas"),
    ("Account Manager", "BNP Paribas"),
    ("Senior Account Manager", "Danske Bank"),
    ("Underwriting Specialist", "Santander Nordics"),
    ("Subject Matter Expert (Local Payment Schemes)", "Revolut"),
    ("Customer Success Manager", "Enode"),
    ("Inside Sales Representative", "Future Electronics"),
    ("Customer Service Specialist", "EssilorLuxottica"),
    ("Facilities Coordinator", "CBRE"),
    ("Customer Experience Customer Success Specialist, Splunk", "Cisco"),
    ("Support Representative", "Monil"),
]

jobs = json.load(open('/home/ubuntu/li_jobs_raw.json'))

def pick(title, company, loc_pref=None):
    for j in jobs:
        if j["title"].strip() == title and j["company"].strip() == company:
            if loc_pref is None or loc_pref in j["loc"]:
                return j
    return None

sel = []
for t, c in CANDIDATES:
    j = pick(t, c, "Oslo, Oslo" if (t, c) == ("Technical Customer Service Specialist", "Eaton") else None)
    if not j:
        j = pick(t, c)
    if j:
        sel.append(j)
    else:
        print("NOT FOUND in raw:", t, "|", c)

NOR_PAT = re.compile(r'(flytende|fluent[^\.;]{0,30}(norwegian|norsk)|(norwegian|norsk)[^\.;]{0,40}(fluent|required|proficient|good command|excellent|native)|speak[^\.;]{0,30}norwegian|god(?:e)? beherskelse[^\.;]{0,30}norsk)', re.I)
ENG_PAT = re.compile(r'english', re.I)

out = []
for j in sel:
    page = fetch(j["link"])
    time.sleep(0.8)
    raw, meta = get_desc(page)
    rec = {"title": j["title"], "company": j["company"], "link": j["link"], "loc": j["loc"]}
    if raw is None:
        rec["status"] = "UNAVAILABLE" + (" (loginwall)" if page and ("authwall" in page or "login" in page[:5000].lower()) else "")
        rec["note"] = "page empty or blocked"
        out.append(rec)
        print(f"--- {j['title']} | {j['company']}: UNAVAILABLE")
        continue
    text = strip_html(raw)
    loginwalled = ("authwall" in (page or "")) or ('id="profile-json"' not in (page or "") and len(text) < 200)
    sent = re.split(r'(?<=[\.\!\?])\s+', text)
    nor_sents = [s.strip()[:220] for s in sent if NOR_PAT.search(s)]
    eng_sents = [s.strip()[:220] for s in sent if ENG_PAT.search(s)]
    aao = len(re.findall(r'[æøåÆØÅ]', text))
    rec.update({
        "status": "OK",
        "len": len(text),
        "aao": aao,
        "nor_sents": nor_sents[:4],
        "eng_sents": eng_sents[:4],
        "posted": meta.get("posted", ""),
        "valid_through": meta.get("valid_through", ""),
        "excerpt": text[:600],
    })
    out.append(rec)
    print(f"=== {j['title']} | {j['company']} | {j['loc']}")
    print(f"    len={len(text)} æøå={aao} posted={meta.get('posted','?')}")
    print(f"    NOR-REQ: {nor_sents[:3]}")
    print(f"    ENGLISH: {eng_sents[:3]}")
    print(f"    EXCERPT: {text[:280]}")
    print()

json.dump(out, open('/home/ubuntu/spotcheck.json', 'w'), indent=1, ensure_ascii=False)
print("SPOTCHECK DONE:", len(out))
