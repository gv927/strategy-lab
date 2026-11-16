#!/usr/bin/env python3
"""Assess cached finn Oslo detail pages: English-language & no Norwegian requirement."""
import json, os, re, sys, glob

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
CACHE = f"{WORKDIR}/finn_detail_cache"
WS_RE = re.compile(r"\s+")

NOR_REQ_PATS = [
    r"flytende\s+(?:i\s+)?norsk", r"norsk\s+flytende", r"fluen\w*\s+in\s+norwegian",
    r"norwegian\s+fluen\w*", r"god\s+(?:i\s+)?norsk", r"gode\s+norsk", r"good\s+norwegian",
    r"proficien\w*\s+in\s+norwegian", r"norwegian\s+proficien\w*",
    r"norsk(?:e)?\s+og\s+engelsk", r"engelsk\s+og\s+norsk", r"norsk\s+eller\s+engelsk",
    r"engelsk\s+eller\s+norsk", r"skandinavis\w*\s+(?:språk|language)", r"ett\s+skandinavisk",
    r"et\s+skandinavisk", r"nordisk\s+språk", r"scandinavian\s+language", r"nordic\s+language",
    r"norsk(?:e)?\s+språk", r"behersk\w*", r"like\s+trygg\s+på\s+norsk",
    r"snakker\s+og\s+skriver\s+norsk", r"skriftlig\w*[^.\n]{0,40}norsk",
    r"working\s+language\s+will\s+be\s+norwegian", r"everyday\s+working\s+language",
    r"norwegian\s+on\s+a\s+fluent", r"norwegian\s+language\s+skills", r"norsk\s+språkkunnskap",
    r"norsk\s+er\s+arbeidsspråk", r"arbeidsspråk[^.\n]{0,40}norsk",
    r"norsk[^.\n]{0,30}ferdigheter", r"erfarenhet\s+med\s+norsk", r"norsk\w*\s+som\s+arbeidsspråk",
    r"språk[^.\n]{0,50}norsk", r"norsk[^.\n]{0,50}språk",
    r"krav[^.\n]{0,60}norsk", r"norsk[^.\n]{0,60}(?:krav|påkrevd|required|må beherskes|må kunne)",
    r"norsk[^.\n]{0,30}(?:er\s+et\s+krav|påkrevd)", r"norsktalende", r"norsk\s+talende",
    r"du\s+snakker\s+norsk", r"snakker\s+norsk", r"behandler\s+norsk",
]
OTHER_PATS = [
    r"sprichst\s+du\s+deutsch", r"german\s+language", r"kenntnisse\w*\s+deutsch",
    r"fransk[^.\n]{0,20}(?:språk|krav)", r"french\s+language", r"svenska?\s+flytende",
    r"italiensk[^.\n]{0,15}krav", r"italian\s+language",
]

NOR_MARKERS = [
    r"\bvi\s+søker\b", r"\bvi\s+tilbyr\b", r"\bhva\s+vi\s+tilbyr\b", r"\bkvalifikasjoner\b",
    r"\bønskede\s+kvalifikasjoner\b", r"\barbeidsoppgaver\b", r"\bfremstillingsevner\b",
    r"\bom\s+du\b", r"\bdin\b", r"\bdu\s+kan\b", r"\bkontakt\s+oss\b", r"\bsøknadsfrist\b",
    r"\barbeidsspråk\b", r"\ber\s+du\s+en\b", r"\blønner\s+du\b", r"\bvi\s+kan\s+tilbyr\b",
    r"\bhar\s+du\b", r"\bseriøs\b", r"\bansvar\b", r"\bkrav\s+til\b", r"\bvi\s+ser\s+fram\b",
    r"\bsamarbeid\b", r"\bansatte\b", r"\bmøte\b", r"\berfaring\b", r"\butdannelse\b",
    r"\bkunder\b", r"\bselskap\b", r"\bkontaktperson\b", r"\btilbakebudskap\b",
    r"\bsamarbeidsvillig\b", r"\bengasjement\b", r"\bvi\s+tilbyr\s+deg\b", r"\bdine\b",
    r"\bhvor\b", r"\bderfor\b", r"\bogså\b", r"\bblant\s+annet\b", r"\bslikt\b", r"\bblant\b",
    r"\bdu\s+vil\b", r"\bvi\s+gjør\b", r"\bnye\b", r"\bgammel\b", r"\bmest\b", r"\bhva\s+vi\b",
]
EN_MARKERS = [
    r"\bwe\s+are\s+looking\s+for\b", r"\bwe\s+offer\b", r"\bour\s+team\b", r"\bthe\s+role\b",
    r"\bresponsibilities\b", r"\bqualifications\b", r"\brequirements\b", r"\bwhat\s+we\s+offer\b",
    r"\babout\s+the\s+role\b", r"\byou\s+will\b", r"\bapply\b", r"\bwe\s+hire\b",
    r"\bkey\s+responsibilit", r"\bthe\s+candidate\b", r"\bstrong\s+commercial\b",
    r"\bdeliver\b", r"\bexperience\s+in\b", r"\bwork\s+with\b", r"\bjoin\s+us\b",
    r"\bgood\s+working\s+knowledge\b", r"\bkey\s+skills\b", r"\babout\s+us\b", r"\bwhy\s+join\b",
    r"\bmain\s+responsibilit", r"\bpreferred\s+qualifications\b", r"\bgood\s+command\s+of\b",
]

def windows(text, pat, w=120):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def is_english_title(t):
    nor_chars = set("æøåÆØÅ")
    if any(c in nor_chars for c in t): return False
    return True

def assess(d):
    body = d.get("body","")
    info = d.get("info",{}) or {}
    wl = ""
    for k,v in info.items():
        kl = k.lower()
        if "arbeidsspr" in kl or kl.startswith("språk"):
            wl = v
    nor_req = []
    for p in NOR_REQ_PATS:
        for w in windows(body,p):
            nor_req.append(w)
    other = []
    for p in OTHER_PATS:
        for w in windows(body,p):
            other.append(w)
    nm = sum(1 for p in NOR_MARKERS if re.search(p, body, re.I))
    em = sum(1 for p in EN_MARKERS if re.search(p, body, re.I))
    return {**{k:d.get(k) for k in ("id","url","title","company","location","date")},
            "wl":wl, "nor_req":nor_req, "other":other, "nm":nm, "em":em,
            "body_len":d.get("body_len",0), "body":body}

def main():
    rows = []
    for f in glob.glob(f"{CACHE}/*.json"):
        d = json.load(open(f))
        rows.append(assess(d))
    json.dump(rows, open(f"{WORKDIR}/finn_assessed.json","w"), ensure_ascii=False, indent=1)
    # candidates: no Norwegian requirement hits, English markers >= Norwegian markers
    cand = [r for r in rows if not r["nor_req"] and not r["other"] and r["em"] >= r["nm"] and r["em"] >= 2]
    print("total cached:", len(rows), "candidates:", len(cand))
    for r in sorted(cand, key=lambda x: x["date"], reverse=True):
        print(f"{r['id']} | {r['title'][:60]:60} | {r['company'][:24]:24} | {r['date'][:10]} | wl={r['wl'][:20]:20} | en={r['em']} no={r['nm']} len={r['body_len']}")
    json.dump(cand, open(f"{WORKDIR}/finn_candidates.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
