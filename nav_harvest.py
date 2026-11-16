#!/usr/bin/env python3
"""Harvest NAV search API for Oslo ads matching candidate profile keywords. Saves to nav_hits.json."""
import json, time, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE = "https://arbeidsplassen.nav.no/stillinger/api/search"

def api(params):
    url = BASE + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                print("FAIL", params, e)
                return None
            time.sleep(2)

QUERIES = [
    {},
    {"q": "customer service"},
    {"q": "customer support"},
    {"q": "customer success"},
    {"q": "bank"},
    {"q": "banking"},
    {"q": "finance"},
    {"q": "financial"},
    {"q": "sales"},
    {"q": "marketing"},
    {"q": "kundeservice"},
    {"q": "english"},
]

hits = {}
for q in QUERIES:
    params = dict(q)
    params["county"] = "OSLO"
    total = None
    for page in range(6):
        params["from"] = str(page * 25)
        d = api(params)
        if d is None:
            break
        if total is None:
            total = d["hits"]["total"]["value"]
            print("QUERY", params.get("q", "(none)"), "TOTAL:", total, flush=True)
        batch = d["hits"]["hits"]
        if not batch:
            break
        for h in batch:
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
                "q": params.get("q", ""),
            }
        if (page + 1) * 25 >= total:
            break
        time.sleep(0.3)

# international=true alone (all countries, filter later)
params = {"international": "true"}
for page in range(4):
    params["from"] = str(page * 25)
    d = api(params)
    if d is None:
        break
    batch = d["hits"]["hits"]
    if not batch:
        break
    for h in batch:
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
            "q": "INTERNATIONAL",
        }

out = list(hits.values())
with open("/home/ubuntu/nav_hits.json", "w") as f:
    json.dump(out, f, ensure_ascii=False)
print("SAVED", len(out), "unique ads")
