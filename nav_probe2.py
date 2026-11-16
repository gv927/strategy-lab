#!/usr/bin/env python3
"""Probe: county=OSLO total vs international=true effects and pagination params."""
import json, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def api(params):
    url = "https://arbeidsplassen.nav.no/stillinger/api/search?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

for p in [
    {"county": "OSLO"},
    {"international": "true"},
    {"international": "true", "county": "OSLO"},
    {"international": "true", "county": "OSLO", "page": "2"},
    {"international": "true", "county": "OSLO", "from": "25"},
]:
    d = api(p)
    total = d["hits"]["total"]["value"]
    n = len(d["hits"]["hits"])
    first_uuids = [h["_id"] for h in d["hits"]["hits"][:3]]
    print(p, "-> TOTAL:", total, "RETURNED:", n, "FIRST:", first_uuids)
