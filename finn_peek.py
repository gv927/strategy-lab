#!/usr/bin/env python3
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
det = json.load(open(f"{WORKDIR}/finn_details.json"))
d = det[0]
print("URL:", d["url"])
print("INFO:", json.dumps(d["info"], ensure_ascii=False, indent=1))
print("---- BODY (first 2500 chars) ----")
print(d["body"][:2500])
print("---- len:", d["body_len"])
