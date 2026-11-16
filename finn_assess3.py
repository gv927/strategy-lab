#!/usr/bin/env python3
"""Full assessment of Oslo finn ads: English-body detection + Norwegian-requirement kill."""
import json, re, sys

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

# --- Norwegian / other-language REQUIREMENT patterns (kill list) ---
NOR_REQ = [
    r"flytende\s+(?:i\s+)?norsk", r"norsk\s+flytende", r"fluen\w*\s+i\s+norwegian",
    r"fluen\w*\s+in\s+norwegian", r"norwegian\s+fluen\w*",
    r"god\s+i\s+norsk", r"gode\s+norsk", r"gods\s+norsk", r"good\s+norwegian",
    r"proficien\w*\s+in\s+norwegian", r"norwegian\s+proficien\w*",
    r"norsk(?:e)?\s+og\s+engelsk", r"engelsk\s+og\s+norsk", r"norsk\s+eller\s+engelsk",
    r"engelsk\s+eller\s+norsk", r"skandinavis\w*\s+(?:språk|language)", r"ett\s+skandinavisk",
    r"et\s+skandinavisk", r"nordisk\s+språk", r"scandinavian\s+language", r"nordic\s+language",
    r"norsk(?:e)?\s+språk", r"behersk\w*", r"like\s+trygg\s+på\s+norsk",
    r"snakker\s+og\s+skriver\s+norsk", r"skriftlig\w*[^.\n]{0,50}norsk",
    r"working\s+language\s+will\s+be\s+norwegian", r"everyday\s+working\s+language",
    r"norwegian\s+on\s+a\s+fluent", r"norwegian\s+language\s+skills", r"norsk\s+språkkunnskap",
    r"norsk\s+er\s+arbeidsspråk", r"arbeidsspråk[^.\n]{0,40}norsk",
    r"norsk[^.\n]{0,30}ferdigheter", r"erfarenhet\s+med\s+norsk",
    r"norsk\w*\s+som\s+arbeidsspråk", r"språk[^.\n]{0,60}norsk", r"norsk[^.\n]{0,60}språk",
    r"krav[^.\n]{0,70}norsk", r"norsk[^.\n]{0,70}(?:krav|påkrevd|required|må\s+beherskes|må\s+kunne)",
    r"norsk[^.\n]{0,40}(?:er\s+et\s+krav|påkrevd)", r"norsktalende", r"norsk\s+talende",
    r"du\s+snakker\s+norsk", r"snakker\s+norsk", r"behandler\s+norsk", r"skriver\s+norsk",
    r"norsk\s+forståelse", r"forståelse\s+av\s+norsk", r"norsk\s+ferdigheter",
    r"språklig\s+ferdighet[^.\n]{0,40}norsk", r"norsk\s+og\s+engelsk[^.\n]{0,40}(?:språk|kræv|krav)",
]
OTHER_REQ = [
    r"sprichst\s+du\s+deutsch", r"german\s+language", r"kenntnisse\w*\s+deutsch",
    r"fransk[^.\n]{0,25}(?:språk|krav)", r"french\s+language", r"svenska?\s+flytende",
    r"italiensk[^.\n]{0,20}krav", r"italian\s+language", r"polsk[^.\n]{0,15}(?:språk|krav)",
]
# --- Norwegian-language markers (to detect Norwegian-written ads) ---
NOR_MARK = [
    r"\bvi\s+søker\b", r"\bvi\s+tilbyr\b", r"\bhva\s+vi\s+tilbyr\b", r"\bkvalifikasjoner\b",
    r"\bønskede\s+kvalifikasjoner\b", r"\barbeidsoppgaver\b", r"\bfremstillingsevner\b",
    r"\bom\s+du\b", r"\bdin\b", r"\bdu\s+kan\b", r"\bkontakt\s+oss\b", r"\bsøknadsfrist\b",
    r"\barbeidsspråk\b", r"\ber\s+du\s+en\b", r"\blønner\s+du\b", r"\bvi\s+kan\s+tilbyr\b",
    r"\bhar\s+du\b", r"\bseriøs\b", r"\bansvar\b", r"\bkrav\s+til\b", r"\bvi\s+ser\s+fram\b",
    r"\bsamarbeid\b", r"\bansatte\b", r"\bmøte\b", r"\berfaring\b", r"\butdannelse\b",
    r"\bkunder\b", r"\bselskap\b", r"\bkontaktperson\b", r"\btilbakebudskap\b",
    r"\bsamarbeidsvillig\b", r"\bengasjement\b", r"\bvi\s+tilbyr\s+deg\b", r"\bdine\b",
    r"\bhvor\b", r"\bderfor\b", r"\bogså\b", r"\bblant\s+annet\b", r"\bslikt\b",
    r"\bdu\s+vil\b", r"\bvi\s+gjør\b", r"\bnye\b", r"\bmest\b", r"\bhva\s+vi\b",
    r"\bstillingen\b", r"\bkvalifikasjonene\b", r"\boppdraget\b", r"\btilbys\b",
    r"\bmå\s+være\b", r"\bønske\s+vi\b", r"\btenker\s+du\b", r"\bseriøst\b",
]
EN_MARK = [
    r"\bwe\s+are\s+looking\s+for\b", r"\bwe\s+offer\b", r"\bour\s+team\b", r"\bthe\s+role\b",
    r"\bresponsibilities\b", r"\bqualifications\b", r"\brequirements\b", r"\bwhat\s+we\s+offer\b",
    r"\babout\s+the\s+role\b", r"\byou\s+will\b", r"\bapply\b", r"\bwe\s+hire\b",
    r"\bkey\s+responsibilit", r"\bthe\s+candidate\b", r"\bstrong\s+commercial\b",
    r"\bdeliver\b", r"\bexperience\s+in\b", r"\bwork\s+with\b", r"\bjoin\s+us\b",
    r"\bgood\s+working\s+knowledge\b", r"\bkey\s+skills\b", r"\babout\s+us\b",
    r"\bwhy\s+join\b", r"\bmain\s+responsibilit", r"\bpreferred\s+qualifications\b",
    r"\bgood\s+command\s+of\b", r"\byou\s+have\b", r"\bwe\s+are\b", r"\bthe\s+company\b",
    r"\bwhat\s+you\s+will\b", r"\bwho\s+you\s+are\b", r"\byour\s+profile\b",
]

def windows(text, pat, w=120):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def assess(d):
    body = d.get("body","")
    info = d.get("info",{}) or {}
    wl = ""
    for k,v in info.items():
        kl = k.lower()
        if "arbeidsspr" in kl or kl.startswith("språk"):
            wl = v
    nor_req = []
    for p in NOR_REQ:
        for w in windows(body,p):
            nor_req.append(w)
    other = []
    for p in OTHER_REQ:
        for w in windows(body,p):
            other.append(w)
    nm = sum(1 for p in NOR_MARK if re.search(p, body, re.I))
    em = sum(1 for p in EN_MARK if re.search(p, body, re.I))
    return {**{k:d.get(k) for k in ("id","url","title","company","location","date")},
            "wl":wl, "nor_req":nor_req, "other":other, "nm":nm, "em":em,
            "body_len":d.get("body_len",0), "body":body}

def main():
    rows = [assess(d) for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))]
    json.dump(rows, open(f"{WORKDIR}/finn_assessed_all.json","w"), ensure_ascii=False, indent=1)
    cand = [r for r in rows if not r["nor_req"] and not r["other"] and r["em"] >= 2 and r["em"] >= r["nm"]]
    print("total:", len(rows), "| no-nor-req + english-ish:", len(cand))
    for r in sorted(cand, key=lambda x: x["date"], reverse=True):
        print(f"{r['id']} | {r['title'][:58]:58} | {r['company'][:22]:22} | {r['date'][:10]} | wl={r['wl'][:18]:18} | en={r['em']} no={r['nm']} | len={r['body_len']}")
    json.dump(cand, open(f"{WORKDIR}/finn_cand_all.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
