#!/usr/bin/env python3
"""Scan ALL Oslo ads for English-looking titles not captured by the title-match filter."""
import json, re
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
det = json.load(open(f"{WORKDIR}/finn_details_all.json"))
short_ids = {r["id"] for r in json.load(open(f"{WORKDIR}/finn_title_short.json"))}
EN_TITLE = re.compile(r"^[A-Za-z0-9'’\-—&/,.()\s]+$")
KEY = re.compile(r"\b(bank|financ|sales|sell|mark|customer|service|support|account|advisor|adviser|"
                  r"consultant|manager|analyst|officer|assistant|coordinator|specialist|associate|"
                  r"executive|representative|advisor|credit|risk|compliance|treasury|insurance|"
                  r"payment|wealth|fund|investment|broker|admin|office|reception|store|shop|"
                  r"business|growth|content|brand|product\s+manager|digital|web|social)\b", re.I)
NOR_CHARS = re.compile(r"[æøåÆØÅ]")
missing = []
for d in det:
    t = d.get("title","") or ""
    if d["id"] in short_ids: continue
    if NOR_CHARS.search(t): continue
    if not KEY.search(t): continue
    body = d.get("body","")
    if len(body) < 400: continue
    missing.append((d["date"][:10], t, d.get("company",""), d["id"], d.get("info",{}).get("Arbeidsspråk","")))
missing.sort(reverse=True)
print("English-looking title ads NOT in title-match set:", len(missing))
for m in missing:
    print(f"{m[0]} | {m[1][:70]:70} | {m[2][:22]:22} | wl={m[4][:16]:16} | {m[3]}")
