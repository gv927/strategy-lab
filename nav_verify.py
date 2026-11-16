#!/usr/bin/env python3
"""Fetch full ad text for shortlisted UUIDs; detect language and Norwegian requirements."""
import re, html, json, time, sys, urllib.request

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
    "8da2db8d-178b-4c06-ad5f-723ea7f59630": "IT Support Specialist (Sperton)",
    "dd7e73ec-a735-4cc6-b79f-dc48562d998f": "Account Executive Mid-Market (ReWind)",
    "22cf15b6-9932-4a28-9f72-70cea038e63c": "Business Developer Mid-Market (ReWind)",
    "9d8033f2-27b8-4bfb-a1e0-d239cefb9acb": "Support Representative (Monil)",
    "f0b9714d-da8f-47b9-a177-be3066980a52": "Customer Success (Availy)",
    "ca7484e6-3c6b-4ae9-b50b-298d8448fd13": "Business Manager (Arval)",
    "886eed1f-ed53-48e6-9934-1ba5acd75f43": "Lead Account Executive (BrightAnalytics)",
    "0058682d-d9c1-4983-8f13-361fa0235409": "AML konsulent KLP (Adecco)",
    "c11a7a9b-fc61-424d-96c8-04fdb22294d8": "Private Banker (Nordea)",
    "ea99344d-2533-4dcf-86e9-fb7942a8229d": "Kunderådgiver bank (Landkreditt)",
    "94fa03c0-96b9-4e2b-aba4-7b64942a2001": "Salg finans karriere (Loyalty)",
    "4e1c6ee3-bd2f-4662-b27f-6fd4d5cc88fe": "Internasjonalt selskap (Add Persona)",
    "c178c77f-4a40-4db5-9515-0d1988680d5a": "Consulting Sales Director bank (Sperton)",
    "9f2384ca-d75e-4ced-8b07-f7c631352cfd": "European power market (Euronext)",
    "73aff703-5165-4cd4-9cef-9baabef11083": "Business Development Manager (Superb)",
}

NOR_PAT = re.compile(r"(flytende norsk|flytande norsk|flytande|godt norsk|gode norskkunnskaper|god norskkunnskaper|krever norsk|norsk språk|norskkunnskap|fluent norwegian|master norwegian|native norwegian|excellent norwegian|proficient in norwegian|norwegian language|in norwegian|på norsk|nivå C1 norsk|B2 norsk|svensk og|dansk og)", re.I)
ENG_PAT = re.compile(r"(english|engelsk)", re.I)

out = {}
for u, label in UUIDS.items():
    url = BASE + u
    try:
        raw = fetch(url)
    except Exception as e:
        print("### FAIL", label, e)
        continue
    text = visible_text(raw)
    # Trim boilerplate: start at title-ish; find "Om jobben" or use from beginning after cookie text
    i = text.find("Hopp til innhold")
    if i >= 0:
        text = text[i:]
    out[u] = text
    print("#" * 70)
    print("### AD:", label, "|", url)
    print("LEN:", len(text))
    m = re.search(r"Arbeidsgiver\s+(.{0,80}?)\s+Sted\s+(.{0,80}?)\s+Om jobben", text)
    if m:
        print("EMP/LOC:", m.group(1)[:60], "|", m.group(2)[:60])
    # deadline
    dl = re.search(r"Søk senest ([\w\s\.]+?)(?:Job overview|Søk på jobben|$)", text)
    print("DEADLINE:", dl.group(1)[:50] if dl else "?")
    # language mentions
    nor = NOR_PAT.findall(text)
    print("NORWEGIAN-MENTIONS:", [n[:40] for n in nor[:8]])
    # language requirement snippets
    for mm in re.finditer(r"(?i)([^.]{0,120}(norsk|norwegian|engelsk|english|språk|language)[^.]{0,120}\.)", text):
        s = mm.group(0).strip()
        if len(s) > 30:
            print("  LANG>", s[:240])
    # expired?
    if re.search(r"utløpt|expired", text, re.I):
        print("  ** EXPIRED MARKER **")
    time.sleep(1.5)

with open("/home/ubuntu/nav_ads_text.json", "w") as f:
    json.dump(out, f, ensure_ascii=False)
print("saved", len(out), "ad texts")
