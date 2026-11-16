#!/usr/bin/env python3
"""Batch 3 verification: final candidate ads."""
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
    "2105bb10-c6d5-4845-964a-bb249d8282a9": "SIX ROBOTICS Strategic Account Executive",
    "d20491fd-9a96-44e2-802d-4acc3d7b4a3d": "HOXTON OSLO",
    "e3a0f7c4-33ac-45dd-8934-21193d1a2b79": "00SMART Independent Sales Partner",
    "ef879264-ca96-4ccd-9f67-257d93f63d30": "APPFARM Head of Content Marketing",
    "ed0713a2-8624-4802-a428-12bc28867797": "NO ISOLATION Head of Sales",
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
    j = text.find("Skriv en kort tilbakemelding")
    if j > 0:
        text = text[:j]
    out[u] = text
    print("=" * 90)
    print("AD:", label, "|", BASE + u)
    ws = re.search(r"Arbeidsspråk\s+([^\s].{0,30}?)\s+(Vis flere|Søk|Mulighet)", text)
    print("WORKLANG:", ws.group(1)[:40] if ws else "?")
    print("EXPIRED" if re.search(r"utløpt|expired", text, re.I) else "ACTIVE")
    # norwegian requirements
    for mm in re.finditer(r"(?i)([^.]{0,100}(flytende norsk|flytande|godt norsk|gode norsk|god norsk|norsk kunnskap|norwegian|swedish|svensk)[^.]{0,120}\.)", text):
        print("  NOR>", mm.group(0).strip()[:230])
    print(text[:1100])
    print()
    time.sleep(1.5)

with open("/home/ubuntu/nav_ads_text3.json", "w") as f:
    json.dump(out, f, ensure_ascii=False)
print("saved", len(out))
