#!/usr/bin/env python3
"""Print full ad text for specific ads needing closer inspection."""
import json, re, sys

with open("/home/ubuntu/nav_ads_text.json") as f:
    ads = json.load(f)

keys = sys.argv[1:] if len(sys.argv) > 1 else list(ads.keys())
for k in keys:
    label = {
        "f0b9714d-da8f-47b9-a177-be3066980a52": "AVAILY Customer Success",
        "ca7484e6-3c6b-4ae9-b50b-298d8448fd13": "ARVAL Business Manager",
        "886eed1f-ed53-48e6-9934-1ba5acd75f43": "BRIGHTANALYTICS Lead AE",
        "0058682d-d9c1-4983-8f13-361fa0235409": "KLP AML konsulent",
        "c11a7a9b-fc61-424d-96c8-04fdb22294d8": "NORDEA Private Banker",
        "94fa03c0-96b9-4e2b-aba4-7b64942a2001": "LOYALITY salg finans",
        "9f2384ca-d75e-4ced-8b07-f7c631352cfd": "EURONEXT power market",
        "dd7e73ec-a735-4cc6-b79f-dc48562d998f": "REWIND Account Executive",
        "8da2db8d-178b-4c06-ad5f-723ea7f59630": "SPERTON IT Support Specialist",
        "22cf15b6-9932-4a28-9f72-70cea038e63c": "REWIND Business Developer",
    }.get(k, k[:8])
    print("=" * 80)
    print("AD:", label)
    t = ads[k]
    # cut footer
    for marker in ["Skriv en kort tilbakemelding", "Nyttige artikler for jobbsøkere"]:
        i = t.find(marker)
        if i > 0:
            t = t[:i]
    print(t[:4200])
    print()
