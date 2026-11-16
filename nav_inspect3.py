#!/usr/bin/env python3
"""Check Six Robotics and Appfarm requirements."""
import json, re

with open("/home/ubuntu/nav_ads_text3.json") as f:
    ads = json.load(f)

for k, label in [("2105bb10-c6d5-4845-964a-bb249d8282a9", "SIX ROBOTICS"), ("ef879264-ca96-4ccd-9f67-257d93f63d30", "APPFARM")]:
    t = ads[k]
    print("=" * 80)
    print("AD:", label)
    for marker in ["What you bring", "What You Bring", "you bring", "You have", "you have", "requirements", "Requirements", "qualifications", "Qualifications", "Who you are", "experience", "Experience"]:
        i = t.find(marker)
        if i > 0:
            print(">>>", t[i:i+1500])
            break
    for mm in re.finditer(r"(?i)([^.]{0,100}(norsk|norwegian|engelsk|english)[^.]{0,120}\.)", t):
        s = mm.group(0).strip()
        if len(s) > 40:
            print("  LANG>", s[:230])
