#!/usr/bin/env python3
"""Second harvest pass with rate limiting for remaining keyword queries. Appends to nav_hits.json."""
import json, time, urllib.request, urllib.parse, urllib.error

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE = "https://arbeidsplassen.nav.no/stillinger/api/search"

def api(params):
    url = BASE + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(15)
            else:
                print("HTTP", e.code, params)
                return None
        except Exception as e:
            print("ERR", e)
            time.sleep(5)
    return None

with open("/home/ubuntu/nav_hits.json") as f:
    hits = {h["uuid"]: h for h in json.load(f)}
print("loaded", len(hits))

def add(d, q):
    for h in d["hits"]["hits"]:
        s = h["_source"]
        u = s.get("uuid") or h["_id"]
        if u in hits:
            continue
        hits[u] = {
            "uuid": u,
            "title": s.get("title", ""),
            "employer": (s.get("employer") or {}).get("name", ""),
            "cities": sorted({str(l.get("city")).strip() for l in s.get("locationList", []) if l.get("city")}),
            "counties": sorted({str(l.get("county")).strip() for l in s.get("locationList", []) if l.get("county")}),
            "municipals": sorted({str(l.get("municipal")).strip() for l in s.get("locationList", []) if l.get("municipal")}),
            "published": s.get("published", ""),
            "expires": s.get("expires", ""),
            "source": s.get("source", ""),
            "medium": s.get("medium", ""),
            "remote": s.get("remote", False),
            "jobtitle": (s.get("jobTitle") or ""),
            "occupation": [ (o.get("level1") or "") + " / " + (o.get("level2") or "") for o in s.get("occupationList", [])][:3],
            "summary": ((s.get("generatedSearchMetadata") or {}).get("shortSummary") or "")[:400],
            "q": q,
        }

QUERIES = [
    ("bank", {"q": "bank", "county": "OSLO"}),
    ("banking", {"q": "banking", "county": "OSLO"}),
    ("finance", {"q": "finance", "county": "OSLO"}),
    ("financial", {"q": "financial", "county": "OSLO"}),
    ("sales", {"q": "sales", "county": "OSLO"}),
    ("marketing", {"q": "marketing", "county": "OSLO"}),
    ("kundeservice", {"q": "kundeservice", "county": "OSLO"}),
    ("english", {"q": "english", "county": "OSLO"}),
    ("INTERNATIONAL", {"international": "true"}),
    ("customer success", {"q": "customer success", "county": "OSLO"}),
]

for name, params in QUERIES:
    total = None
    for page in range(4):
        p = dict(params)
        p["from"] = str(page * 25)
        d = api(p)
        if d is None:
            break
        if total is None:
            total = d["hits"]["total"]["value"]
            print("QUERY", name, "TOTAL:", total, flush=True)
        batch = d["hits"]["hits"]
        if not batch:
            break
        add(d, name)
        if (page + 1) * 25 >= total:
            break
        time.sleep(2.5)
    time.sleep(2.5)

with open("/home/ubuntu/nav_hits.json", "w") as f:
    json.dump(list(hits.values()), f, ensure_ascii=False)
print("SAVED", len(hits), "unique ads")
