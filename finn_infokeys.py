#!/usr/bin/env python3
import json, collections
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
rows = json.load(open(f"{WORKDIR}/finn_assessed_all.json"))
c = collections.Counter()
for r in rows:
    pass
det = json.load(open(f"{WORKDIR}/finn_details_all.json"))
keys = collections.Counter()
for d in det:
    for k in d.get("info",{}): keys[k]+=1
print("INFO KEYS:", keys.most_common(20))
print()
wl = collections.Counter()
for d in det:
    for k,v in d.get("info",{}).items():
        if "arbeidsspr" in k.lower(): wl[v]+=1
print("ARBEIDSSPRAK VALUES:", wl.most_common(15))
