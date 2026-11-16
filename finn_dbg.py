#!/usr/bin/env python3
import json, re, sys, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("g2", "/home/ubuntu/finn_gate2.py")
g2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(g2)
det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
for i in sys.argv[1:]:
    body = det[i]["body"]
    hard, soft = g2.evaluate(body)
    print("="*100)
    print(i, det[i]["title"])
    print("HARD:", len(hard))
    for h in hard[:4]: print("   H:", h[:220])
    print("SOFT:", len(soft))
    for s in soft[:4]: print("   S:", s[:220])
    # show the raw sentences containing Norwegian
    for sent in g2.sentences(body):
        if re.search(r"norsk|norwegian", sent, re.I) and re.search(r"fluen|proficien|krav|språk|language", sent, re.I):
            print("   SENT:", sent[:250])
            break
