#!/usr/bin/env python3
"""Dump focused verification details for specific ad IDs."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")
det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}

ids = sys.argv[1:]
pat = r"(norsk|norwegian|english|engelsk|språk|language|fluen\w*|proficien\w*|behersk\w*|scandinav\w*|nordisk|native|degree|years of experience)"
for i in ids:
    d = det.get(i)
    if not d:
        print("MISSING", i); continue
    print("="*110)
    print(f"{d['title']}\n{d.get('company','')} | {d.get('location','')} | {d.get('date','')[:10]} | info={d.get('info',{})}\n{d['url']}")
    body = d.get("body","")
    seen = []
    for m in re.finditer(pat, body, re.I):
        a = max(0, m.start()-120); b = min(len(body), m.end()+120)
        w = WS_RE.sub(" ", body[a:b].replace("\n"," "))
        if w not in seen:
            seen.append(w)
    for w in seen[:10]:
        print("   ...", w)
    print("  --HEAD--")
    print("   " + body[:900].replace("\n", "\n   "))
