#!/usr/bin/env python3
"""Query NAV search API: international + Oslo, print compact results."""
import json, sys, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def api(params):
    url = "https://arbeidsplassen.nav.no/stillinger/api/search?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

if __name__ == "__main__":
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"international": "true", "county": "OSLO"}
    d = api(params)
    print("PARAMS:", params)
    print("TOTAL:", d["hits"]["total"]["value"])
    for h in d["hits"]["hits"]:
        s = h["_source"]
        loc = ";".join(sorted({str(l.get("city")) for l in s.get("locationList", []) if l.get("city")}))
        print("-TITLE:", s.get("title"))
        print("  EMP:", s.get("employer", {}).get("name"))
        print("  LOC:", loc)
        print("  UUID:", s.get("uuid"))
        print("  SRC:", s.get("source"), "|", s.get("medium"))
        print("  OCC:", [o.get("level1") + "/" + str(o.get("level2")) for o in s.get("occupationList", [])][:3])
        summ = (s.get("generatedSearchMetadata") or {}).get("shortSummary", "")
        print("  SUMMARY:", summ[:280])
