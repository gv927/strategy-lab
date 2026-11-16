#!/usr/bin/env python3
"""Language triage for finn ad bodies: English-only, no Norwegian requirement."""
import json, re, sys

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"

# --- Norwegian-language requirement detectors (body text) ---
NOR_REQ = [
    r"flytende\s+norsk", r"norsk\s+flytende", r"fluent\s+in\s+norwegian", r"fluency\s+in\s+norwegian",
    r"god\s+norsk", r"gode\s+norsk", r"very\s+good\s+norwegian", r"good\s+norwegian",
    r"proficien\w*\s+in\s+norwegian", r"norwegian\s+proficien\w*",
    r"norsk(?:e)?\s+og\s+engelsk", r"engelsk\s+og\s+norsk", r"norsk\s+eller\s+engelsk",
    r"engelsk\s+eller\s+norsk", r"norsk\s+og\s+engelsk\s+", r"skandinavis\w*\s+(?:språk|language)",
    r"ett\s+skandinavisk", r"et\s+skandinavisk", r"nordisk\s+språk", r"scandinavian\s+language",
    r"norsk(?:e)?\s+språk", r"behersk\w*\s+(?:norsk|engelsk\s+og\s+norsk)",
    r"like\s+trygg\s+på\s+norsk", r"snakker\s+og\s+skriver\s+norsk", r"skriftlig\w*\s+kommunikasjonsevner\s+på\s+norsk",
    r"working\s+language\s+will\s+be\s+norwegian", r"everyday\s+working\s+language",
    r"norwegian\s+on\s+a\s+fluent", r"norwegian\s+language\s+skills", r"norsk\s+språkkunnskap",
    r"norsk\s+er\s+arbeidsspråk", r"arbeidsspråk[^\n]{0,40}norsk",
    r"norsk\s+og\W+engelsk\s+", r"språk[^.\n]{0,40}norsk[^.\n]{0,20}(?:kreves|er\s+krav|required)",
    r"krav[^.\n]{0,40}norsk", r"norsk[^.\n]{0,40}(?:krav|påkrevd|required)",
    r"norsk(?:e)?[^.\n]{0,30}ferdigheter", r"erfarenhet\s+med\s+norsk",
]
OTHER_LANG_REQ = [
    r"sprichst\s+du\s+deutsch", r"german\s+language\s+skills", r"kenntnisse\s+in\s+deutsch",
    r"fransk\s+er\s+arbeidsspråk", r"french\s+language\s+skills", r"svenska?\s+flytende",
]

# Norwegian-language markers in body (to detect Norwegian-written ads)
NOR_MARKERS = [
    r"\bvi\s+søker\b", r"\bvi\s+t tilbyr\b", r"\bhva\s+vi\s+tilbyr\b", r"\bkvalifikasjoner\b",
    r"\bønskede\s+kvalifikasjoner\b", r"\barbeidsoppgaver\b", r"\bfremstillingsevner\b",
    r"\bom\s+du\b", r"\bdin\b", r"\bdu\s+kan\b", r"\bkontakt\s+oss\b", r"\bsøknadsfrist\b",
    r"\barbeidsspråk\b", r"\ber\s+du\s+en\b", r"\blønner\s+du\b", r"\bvi\s+kan\s+tilbyr\b",
    r"\bhar\s+du\b", r"\bseriøs\b", r"\bspennende\b", r"\bansvar\b", r"\boppgaver\b",
    r"\bkrav\s+til\b", r"\bvi\s+ser\s+fram\b", r"\bfordeg\b", r"\bsamarbeid\b", r"\bansatte\b",
    r"\bmøte\b", r"\bdrift\b", r"\berfaring\b", r"\butdannelse\b", r"\bmål\b", r"\btjeneste\b",
    r"\bkunder\b", r"\bselskap\b", r"\båpningstider\b", r"\bkontaktperson\b", r"\boppstart\b",
    r"\btilbakebudskap\b", r"\brydige\b", r"\bpersonlig\b", r"\bsamarbeidsvillig\b", r"\bengasjement\b",
]
EN_MARKERS = [
    r"\bwe\s+are\s+looking\s+for\b", r"\bwe\s+offer\b", r"\bour\s+team\b", r"\bthe\s+role\b",
    r"\bresponsibilities\b", r"\bqualifications\b", r"\brequirements\b", r"\bwhat\s+we\s+offer\b",
    r"\babout\s+the\s+role\b", r"\byou\s+will\b", r"\bapply\b", r"\bwe\s+hire\b", r"\bkey\s+responsibilit",
    r"\bthe\s+candidate\b", r"\bstrong\s+commercial\b", r"\bdeliver\b", r"\bexperience\s+in\b",
    r"\bwork\s+with\b", r"\bjoin\s+us\b", r"\bgood\s+working\s+knowledge\b",
]

def windows(text, pat, w=110):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start() - w); b = min(len(text), m.end() + w)
        out.append(text[a:b].replace("\n", " "))
    return out

def score(text):
    """Return (is_mostly_english, nor_hits, en_hits)."""
    nor = sum(1 for p in NOR_MARKERS if re.search(p, text, re.I))
    en = sum(1 for p in EN_MARKERS if re.search(p, text, re.I))
    # lowercase/english-ratio heuristic on word shapes
    return nor, en

def assess(d):
    body = d.get("body", "")
    info = d.get("info", {})
    wl = ""
    for k, v in info.items():
        if "arbeidsspr" in k.lower() or k.lower().startswith("språk"):
            wl = v
    text = body
    nor_req_hits = []
    for p in NOR_REQ:
        for w in windows(text, p):
            nor_req_hits.append((p, w))
    other_req = []
    for p in OTHER_LANG_REQ:
        for w in windows(text, p):
            other_req.append((p, w))
    nor_markers, en_markers = score(text)
    # English signal: ratio of English marker hits vs Norwegian markers
    return {
        "id": d["id"], "url": d["url"], "title": d["title"], "company": d["company"],
        "location": d["location"], "date": d.get("date", ""), "wl": wl,
        "nor_req_hits": nor_req_hits, "other_req": other_req,
        "nor_markers": nor_markers, "en_markers": en_markers,
        "body_len": d.get("body_len", 0),
    }

def main():
    det = json.load(open(f"{WORKDIR}/finn_details.json"))
    res = [assess(d) for d in det]
    json.dump(res, open(f"{WORKDIR}/finn_assess.json","w"), ensure_ascii=False, indent=1)
    for r in res:
        print(f"{r['id']} | {r['title'][:55]:55} | {r['company'][:22]:22} | wl={r['wl'][:22]:22} | nor={r['nor_markers']:2} en={r['en_markers']:2} | noreq={len(r['nor_req_hits'])} other={len(r['other_req'])} | {r['date'][:10]}")
    print("total", len(res))

if __name__ == "__main__":
    main()
