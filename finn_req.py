#!/usr/bin/env python3
"""Print requirement bullets (Kvalifikasjoner section) for shortlisted ads."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}

def req_bullets(body):
    """Return the Kvalifikasjoner short-summary bullets."""
    lines = body.split("\n")
    try:
        i = lines.index("Kvalifikasjoner")
    except ValueError:
        return []
    out = []
    for l in lines[i+1:i+14]:
        if l.strip() in ("Hva vi tilbyr", "Er du en god match for denne stillingen?", "Vis mindre"):
            break
        if l.strip():
            out.append(l.strip())
    return out

def full_body(body, n=2500):
    # body after the short summary
    idx = body.find("Vis hele kortversjonen")
    return body[idx+len("Vis hele kortversjonen"):idx+len("Vis hele kortversjonen")+n] if idx >= 0 else body[:n]

for i in sys.argv[1:]:
    d = det.get(i)
    if not d:
        print("MISSING", i); continue
    body = d.get("body","")
    print("="*110)
    print(f"{d['title']}\n{d.get('company','')} | {d.get('location','')} | posted {d.get('date','')[:10]} | info {d.get('info',{})}\n{d['url']}")
    print("  REQ:", " | ".join(req_bullets(body)[:10]))
    print("  FULL:", " ".join(full_body(body, 900).split())[:900])
