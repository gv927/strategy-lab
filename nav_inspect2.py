#!/usr/bin/env python3
"""Inspect qualification/language sections of batch-2 ads."""
import json, re

with open("/home/ubuntu/nav_ads_text2.json") as f:
    ads = json.load(f)

for k, label in [("1a8a2e35-62cc-4d48-869a-a0170d2517c2", "VZU"), ("d9dabae7-08c5-459c-90b1-aaa7c853f34a", "CYVIZ"), ("288405d4-0e9f-4d0f-b031-868894865d83", "TELAVOX"), ("796356ea-15f6-4edb-87cf-de03c7521772", "PROMON")]:
    t = ads[k]
    print("=" * 80)
    print("AD:", label)
    # print from "requirements/qualifications" style markers onward
    for marker in ["What we’re looking for", "What you'll bring", "Hvem er du", "Hva vi ser etter", "qualifications", "Qualifications", "you have", "You have", "Hvem søker vi", "erfaring", "requirements", "What We’re Looking For", "Who you are", "Det er en fordel"]:
        i = t.find(marker)
        if i > 0:
            print(">>>", t[i:i+1800])
            break
    # any Norwegian mentions
    for mm in re.finditer(r"(?i)([^.]{0,100}(norsk|norwegian|swedish|svensk|scandinavian|skandinav)[^.]{0,120}\.)", t):
        print("  NOR>", mm.group(0).strip()[:220])
