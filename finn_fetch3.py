#!/usr/bin/env python3
"""Fetch details for newly-discovered Oslo cards, merge with existing details."""
import json, os, re, subprocess, sys, time, html
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/ubuntu")
import importlib.util
spec = importlib.util.spec_from_file_location("f2", "/home/ubuntu/finn_fetch2.py")
f2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(f2)

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"

def main():
    cards = json.load(open(f"{WORKDIR}/finn_cards.json"))
    oslo = [c for c in cards if re.search(r"\bOslo\b", c["location"], re.I)]
    details = json.load(open(f"{WORKDIR}/finn_details_all.json"))
    have = {d["id"] for d in details}
    todo = [c for c in oslo if c["id"] not in have]
    print("oslo:", len(oslo), "have:", len(have), "todo:", len(todo), flush=True)
    new = []
    if todo:
        with ThreadPoolExecutor(max_workers=6) as ex:
            for i,(c,page) in enumerate(zip(todo, ex.map(lambda cc: f2.get_html(cc), todo))):
                new.append(f2.parse(page, c))
                if (i+1) % 100 == 0: print("fetched", i+1, flush=True)
    all_det = details + new
    json.dump(all_det, open(f"{WORKDIR}/finn_details_all.json","w"), ensure_ascii=False, indent=1)
    print("total details:", len(all_det), "empty:", sum(1 for d in all_det if d["body_len"] < 200))

if __name__ == "__main__":
    main()
