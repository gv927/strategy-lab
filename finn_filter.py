#!/usr/bin/env python3
import json, re
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
cards = json.load(open(f"{WORKDIR}/finn_cards.json"))
print("total", len(cards))
locs = {}
for c in cards:
    locs[c["location"]] = locs.get(c["location"], 0) + 1
oslo = [c for c in cards if re.search(r"oslo", c["location"], re.I)]
print("oslo", len(oslo))
print("sample locations:", sorted(locs.items(), key=lambda x: -x[1])[:25])
# keyword relevance filter on title
KW = re.compile(r"bank|financ|sales|salg|customer|kunde|market|administra|account|kontor|service|support|økonom|econom|risk|compliance|aml|treasury|advisor|manager|consultant|consult|CRM|relationship|salg", re.I)
rel = [c for c in oslo if KW.search(c["title"])]
print("relevant title", len(rel))
json.dump(rel, open(f"{WORKDIR}/finn_oslo_rel.json", "w"), ensure_ascii=False, indent=1)
for c in rel[:40]:
    print(c["id"], "|", c["title"][:70], "|", c["company"][:30], "|", c["location"], "|", c["date"][:10])
