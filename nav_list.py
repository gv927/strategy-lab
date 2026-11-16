#!/usr/bin/env python3
"""List all SSR cards compactly, grouped, for candidate selection."""
import json

with open("/home/ubuntu/nav_ssr_hits.json") as f:
    cards = json.load(f)

# group by query
byq = {}
for c in cards:
    byq.setdefault(c["q"], []).append(c)

for q in ["international", "english", "customer service", "customer support", "customer success", "bank", "banking", "finance", "financial", "kundeservice", "sales", "marketing"]:
    print("=" * 20, q)
    for c in byq.get(q, []):
        print(f"- {c['title'][:85]}")
        print(f"    EMP: {c['employer'][:50]} | LOC: {c['location'][:60]} | JT: {c['jobtitle'][:50]} | DL: {c['deadline'][:30]}")
        print(f"    {c['uuid']}")
