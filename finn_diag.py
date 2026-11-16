#!/usr/bin/env python3
import json, glob, re
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
files = glob.glob(f"{WORKDIR}/finn_detail_cache/*.json")
print("files", len(files))
rows = [json.load(open(f)) for f in files]
print("body_len stats: zero =", sum(1 for r in rows if r["body_len"] == 0),
      " <500 =", sum(1 for r in rows if 0 < r["body_len"] < 500),
      " >=500 =", sum(1 for r in rows if r["body_len"] >= 500))
r = max(rows, key=lambda x: x["body_len"])
print("=== longest:", r["title"], r["url"], r["body_len"])
print(r["body"][:1500])
print("=== info keys sample:", list(r["info"].items())[:8])
