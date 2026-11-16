#!/usr/bin/env python3
"""Shortlist ads from nav_hits.json matching candidate profile in Oslo."""
import json, re

with open("/home/ubuntu/nav_hits.json") as f:
    hits = json.load(f)
print("total hits:", len(hits))

PROFILE = re.compile(r"(bank|finan|kunde|customer|service|support|success|sales|salg|market|markeds|admin|kontor|advisor|rådgiver|account|reception|resepsjon|consultant|b2b|crm|relationship|kundebehandler|butikk|shop|kasse|retail|business develop|key account|helpdesk|it[- ]support|data|digital)", re.I)
NORW_REQ = re.compile(r"(flytende norsk|flytande|godt norsk|god norsk|norsk flytende|fluent norwegian|master norwegian|norsk på|svært gode norsk|very good norwegian|du må kunne norsk|norsk språk er krav|krever norsk|norwegian language (is )?requir|excellent norwegian|proficient in norwegian|native norwegian|norsk som morsmål|norsk morsmål)", re.I)
ENGLISH_OK = re.compile(r"(english|engelsk)", re.I)

now = "2026-10-27"
short = []
for h in hits:
    txt = (h["title"] + " " + h.get("jobtitle","") + " " + h["summary"])
    # location: Oslo (municipal OSLO or city OSLO) or remote
    oslo = any("OSLO" == c.strip().upper() for c in h["cities"]) or any("OSLO" == m.strip().upper() for m in h["municipals"]) or any("OSLO" == c.strip().upper() for c in h["counties"] if c)
    remote = bool(h.get("remote"))
    if not (oslo or remote):
        continue
    # active check
    if h["expires"][:10] < now:
        continue
    if not PROFILE.search(txt):
        continue
    if NORW_REQ.search(txt):
        continue
    short.append(h)

print("shortlist:", len(short))
for h in sorted(short, key=lambda x: x["published"], reverse=True):
    print("-", h["title"][:90])
    print("  EMP:", h["employer"][:60], "| CITIES:", h["cities"][:3], "| Q:", h["q"], "| REMOTE:", h.get("remote"))
    print("  SUMMARY:", h["summary"][:200])
    print("  UUID:", h["uuid"], "PUB:", h["published"][:10], "EXP:", h["expires"][:10])
    print()
