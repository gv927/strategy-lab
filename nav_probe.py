#!/usr/bin/env python3
"""Probe NAV search API filter param names."""
import json, sys, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def api(params):
    url = "https://arbeidsplassen.nav.no/stillinger/api/search?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

if __name__ == "__main__":
    tests = [
        {"q": "english", "counties": "OSLO", "size": "3"},
        {"q": "english", "municipals": "OSLO", "size": "3"},
        {"q": "english", "by": "OSLO", "size": "3"},
        {"q": "english", "location": "OSLO", "size": "3"},
    ]
    for p in tests:
        try:
            d = api(p)
            cities = []
            for h in d["hits"]["hits"][:6]:
                for l in h["_source"].get("locationList", []):
                    cities.append(l.get("city"))
            print(p, "-> TOTAL:", d["hits"]["total"]["value"], "CITIES:", cities[:12])
        except Exception as e:
            print(p, "-> ERROR:", e)
