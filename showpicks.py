#!/usr/bin/env python3
import json

r1 = json.load(open('/home/ubuntu/spotcheck.json'))
r2 = json.load(open('/home/ubuntu/spotcheck2.json'))
allr = {x["title"] + "||" + x["company"]: x for x in r1 + r2}

PICKS = [
    ("Key Account Manager", "Ocean Technologies Group"),
    ("Senior Client Services Specialist, OEM IVD", "Thermo Fisher Scientific"),
    ("Customer Success Manager", "Enode"),
    ("Inside Sales Representative", "Future Electronics"),
    ("Key Account Manager", "ASICS EMEA"),
    ("Growth & Digital Operations Specialist (Graduate)", "Noteless"),
    ("Growth Manager", "VISOID"),
    ("Global Digital Marketing Manager", "DNV"),
    ("Subject Matter Expert (Local Payment Schemes)", "Revolut"),
    ("(Senior) Account Manager (m/f/d)", "Emerson"),
    ("Marketing Consultant", "Cyviz"),
    ("Founding Growth Marketer", "The Flex"),
    ("Customer Experience Customer Success Specialist, Splunk", "Cisco"),
]

for t, c in PICKS:
    x = allr.get(t + "||" + c)
    if not x:
        print(f"##### {t} | {c}: NOT IN RESULTS")
        continue
    print("#" * 90)
    print("TITLE:", x["title"], "| COMPANY:", x["company"], "| LOC:", x.get("loc"))
    print("LINK:", x["link"])
    print("STATUS:", x.get("status"), "| posted:", x.get("posted"), "| aao:", x.get("aao"))
    print("NOR_SENTS:", x.get("nor_sents"))
    print("ENG_SENTS:", x.get("eng_sents"))
    print("EXCERPT:")
    print(x.get("excerpt", "")[:1200])
    print()
