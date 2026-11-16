#!/usr/bin/env python3
"""READ-ONLY spot-check round 2: retry failed fetches + additional candidates."""
import urllib.request, urllib.error, re, html, json, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 403) and i < tries - 1:
                time.sleep(12 * (i + 1)); continue
            return None
        except Exception:
            if i < tries - 1:
                time.sleep(5); continue
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
            meta["posted"] = ld.get("datePosted", "")
            meta["valid_through"] = ld.get("validThrough", "")
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
    ("Customer Service Coordinator", "3stepIT"),
    ("Sales Development Representative", "Two"),
    ("Sales Coordinator", "EF"),
    ("Account Manager", "BNP Paribas"),
    ("Customer Success Manager", "Enode"),
    ("Inside Sales Representative", "Future Electronics"),
    ("Customer Service Specialist", "EssilorLuxottica"),
    ("Facilities Coordinator", "CBRE"),
    ("Customer Experience Customer Success Specialist, Splunk", "Cisco"),
    ("Support Representative", "Monil"),
    ("Key Account Manager", "Ocean Technologies Group"),
    ("Sales Specialist – Infrastructure Solutions", "Lenovo"),
    ("CRM Manager - Nordics", "SharkNinja"),
    ("Senior Programmatic Specialist", "WPP Media"),
    ("Senior Paid Search Specialist", "dentsu"),
    ("Integrated Campaign Manager", "Jobgether"),
    ("Key Account Manager", "Truesec"),
    ("Power Derivatives", "Euronext"),
    ("Client Executive - Oslo", "Walley"),
    ("Senior Client Services Specialist, OEM IVD", "Thermo Fisher Scientific"),
    ("Paid Social Specialist", "VILLOID"),
    ("Founding Growth Marketer", "The Flex"),
    ("Marketing Consultant", "Cyviz"),
    ("Key Account Manager", "ASICS EMEA"),
    ("Sales Account Manager", "Kinly"),
    ("(Senior) Account Manager (m/f/d)", "Emerson"),
]

jobs = json.load(open('/home/ubuntu/li_jobs_raw.json'))

def pick(title, company):
    for j in jobs:
        if j["company"].strip() == company and j["title"].strip() == title:
            return j
    for j in jobs:
        if j["company"].strip() == company and j["title"].strip().startswith(title):
            return j
    return None

NOR_PAT = re.compile(r'(flytende|fluent[^\.;\n]{0,30}(norwegian|norsk)|(norwegian|norsk)[^\.;\n]{0,40}(fluent|required|proficient|good command|excellent|native|essential)|speak[^\.;\n]{0,30}norwegian|norwegian language skills required|god(?:e)? beherskelse[^\.;\n]{0,30}norsk|norwegian(?:\s+language)?\s+is\s+(?:a\s+)?(?:must|required|essential|advantage))', re.I)
ENG_PAT = re.compile(r'english', re.I)

out = []
for t, c in CANDIDATES:
    j = pick(t, c)
    if not j:
        print("NOT FOUND:", t, "|", c); continue
    page = fetch(j["link"])
    time.sleep(2.0)
    raw, meta = get_desc(page)
    rec = {"title": j["title"], "company": j["company"], "link": j["link"], "loc": j["loc"]}
    if raw is None or len(raw) < 100:
        rec["status"] = "UNAVAILABLE"
        out.append(rec)
        print(f"--- {j['title']} | {j['company']}: UNAVAILABLE")
        continue
    text = strip_html(raw)
    sent = re.split(r'(?<=[\.\!\?])\s+', text)
    nor_sents = [s.strip()[:220] for s in sent if NOR_PAT.search(s)]
    eng_sents = [s.strip()[:220] for s in sent if ENG_PAT.search(s)]
    aao = len(re.findall(r'[æøåÆØÅ]', text))
    rec.update({"status": "OK", "len": len(text), "aao": aao, "nor_sents": nor_sents[:4],
                "eng_sents": eng_sents[:4], "posted": meta.get("posted", ""),
                "valid_through": meta.get("valid_through", ""), "excerpt": text[:600]})
    out.append(rec)
    print(f"=== {j['title']} | {j['company']} | {j['loc']}")
    print(f"    len={len(text)} æøå={aao} posted={meta.get('posted','?')} valid={meta.get('valid_through','?')}")
    print(f"    NOR-REQ: {nor_sents[:3]}")
    print(f"    ENGLISH: {eng_sents[:3]}")
    print(f"    EXCERPT: {text[:300]}")
    print()

json.dump(out, open('/home/ubuntu/spotcheck2.json', 'w'), indent=1, ensure_ascii=False)
print("ROUND2 DONE:", len(out))
