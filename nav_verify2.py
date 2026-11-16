#!/usr/bin/env python3
"""Batch 2 verification: fetch ad text for more candidate UUIDs."""
import re, html, json, time, urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE = "https://arbeidsplassen.nav.no/stillinger/stilling/"

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def visible_text(raw):
    raw2 = re.sub(r"<script[\s\S]*?</script>", " ", raw)
    raw2 = re.sub(r"<style[\s\S]*?</style>", " ", raw2)
    t = re.sub(r"<[^>]+>", " ", raw2)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t)

UUIDS = {
    "796356ea-15f6-4edb-87cf-de03c7521772": "PROMON IT team",
    "1a8a2e35-62cc-4d48-869a-a0170d2517c2": "VZU Performance Marketing Automation",
    "d9dabae7-08c5-459c-90b1-aaa7c853f34a": "CYVIZ Marketing Consultant",
    "199d140b-3eb7-4d4c-9c80-828fbfd97ac2": "NABOGO Junior Event Specialist",
    "288405d4-0e9f-4d0f-b031-868894865d83": "TELAVOX kommersielt blikk",
    "47cfe0c2-e8b3-4ece-a48d-4fce70eedf0e": "DONE.AI",
    "3665d834-0cc4-4e77-958f-88ab330cce58": "PODIMO Creator Manager",
    "bb625574-c7c0-4782-b7f5-e48762de13d2": "CAMREACH Sales development",
    "4cc868e7-7e89-4fcc-8c19-25a897aa0e39": "NETSECURITY Junior Sales",
    "e646adc5-c93b-4ba0-94ce-139f0da5a576": "NORMET Sales Manager",
}

out = {}
for u, label in UUIDS.items():
    try:
        raw = fetch(BASE + u)
    except Exception as e:
        print("FAIL", label, e)
        continue
    text = visible_text(raw)
    i = text.find("Hopp til innhold")
    if i >= 0:
        text = text[i:]
    for marker in ["Skriv en kort tilbakemelding"]:
        j = text.find(marker)
        if j > 0:
            text = text[:j]
    out[u] = text
    print("=" * 90)
    print("AD:", label, "|", BASE + u)
    # key fields
    ws = re.search(r"Arbeidsspråk\s+([^\s].{0,30}?)\s+(Vis flere|Søk|Mulighet)", text)
    print("WORKLANG:", ws.group(1)[:40] if ws else "?")
    dl = re.search(r"Søk senest ([^A-Za-z]{0,3}[\w\s\.]+?)(?:Gå til|$)", text)
    print("DEADLINE:", dl.group(1)[:40] if dl else ("snarest" if "Søk snarest" in text else "?"))
    print(text[:1600])
    print()
    time.sleep(1.8)

with open("/home/ubuntu/nav_ads_text2.json", "w") as f:
    json.dump(out, f, ensure_ascii=False)
print("saved", len(out))
