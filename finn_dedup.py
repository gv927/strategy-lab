#!/usr/bin/env python3
"""Deduplicate and output final shortlist."""
import json

with open("/home/ubuntu/.hermes/cache/scratch/final_shortlist.json") as f:
    data = json.load(f)

# Deduplicate by (title, company) - keep first occurrence (lowest tier)
seen = set()
unique = []
for s in data:
    key = (s["title"], s["company"])
    if key not in seen:
        seen.add(key)
        unique.append(s)

# Also sort by tier then date
unique.sort(key=lambda x: (x["tier"], x["date"]))

with open("/home/ubuntu/.hermes/cache/scratch/final_shortlist.json", "w") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f"Total unique entries: {len(unique)}")
for s in unique:
    print(f"  Tier {s['tier']}: {s['title']} @ {s['company']} ({s['date']})")

with open("/home/ubuntu/.hermes/cache/scratch/final_shortlist.json", "w") as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)