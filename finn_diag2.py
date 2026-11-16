#!/usr/bin/env python3
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
sys.path.insert(0, "/home/ubuntu")
import importlib.util
spec = importlib.util.spec_from_file_location("a3", "/home/ubuntu/finn_assess3.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows = json.load(open(f"{WORKDIR}/finn_assessed_all.json"))
r = [x for x in rows if x["id"] == "479911811"][0]
print(r["title"], "|", r["company"], "| wl:", r["wl"])
print("---- BODY ----")
print(r["body"][:6000])
print("---- which NOR markers matched ----")
for p in m.NOR_MARK:
    mm = re.search(p, r["body"], re.I)
    if mm:
        a=max(0,mm.start()-70); b=min(len(r["body"]),mm.end()+70)
        print(f"  {p!r} -> ...{m.WS_RE.sub(' ', r['body'][a:b])}...")
