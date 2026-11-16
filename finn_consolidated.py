#!/usr/bin/env python3
"""Consolidated final triage over both candidate pools (title-matched + English-title)."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

# language-ability context: Norwegian/Scandinavian next to an ability word
LANG_CTX = re.compile(
    r"(norsk|norwegian|skandinav\w*|scandinav\w*|nordisk|nordic)[^.]{0,50}"
    r"(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|skriver|forstår\w*|ferdighet\w*|"
    r"kompetanse|krav|påkrevd|må\s+(?:kunne|beherske|snakke)|arbeidsspråk|daily\s+working|"
    r"working\s+language|everyday\s+working|kommer\s+du|skill\w*|command|niveau|nivå)|"
    r"(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|skriver|forstår\w*|ferdighet\w*|"
    r"arbeidsspråk|working\s+language|skill\w*|command|proficien\w*|strong|excellent|good|"
    r"solid|niveau|nivå)[^.]{0,50}(norsk|norwegian|skandinav\w*|scandinav\w*|nordisk)|"
    r"norsk\s+og\s+engelsk|(norsk|norwegian)\s+and\s+english|"
    r"english\s+and\s+(norsk|norwegian)|engelsk\s+og\s+norsk|"
    r"(norsk|norwegian)[^.]{0,40}\b(og|and)\b\s*engelsk", re.I)

INCIDENTAL = re.compile(
    r"(Norwegian\s+(public\s+service|defence|defense|armed\s+forces|government|state|municipality|"
    r"company|companies|business|scale-?up|market|markets|industry|sector|customer|customers|"
    r"office|offices|branch|subsidiary|subsidiar\w+|economy|krone|kroner|currency|law|laws|"
    r"act|regulation\w*|authorit\w+|court\w*|embassy|consulate|heritage|culture|society|"
    r"tax|security\s+act|public\s+administration\s+act|bar|attorney|work\s+environment|"
    r"working\s+hours|public\s+holiday\w*|territory|waters|sea|coast|offshore|maritime|"
    r"maintenance|merchant|energy|telecom\w*|airline\w*|bank\w*|finance|financial|"
    r"pension\s+fund|insurance|ship|shipping|forestry|fish|fisher\w*|agricultur\w+|"
    r"construction|standards|practice|practices|residents?|nationality|citizenship|"
    r"north\s+norway|northern\s+norway)|"
    r"Norwegian\s+Security\s+Act|Norsk\s+(titanium|hydro|data|butikk|industri|luftfart|"
    r"verksted|bil|miljø|teknologi|bane|helse|vare|butikk|bank|finans)|"
    r"Norwegian\s+and\s+(?:Nordic|Scandinavian)\b|"
    r"in\s+the\s+Norwegian\s+market|Norwegian\s+offices|Norwegian\s+company|"
    r"Norwegian\s+Public\s+Service\s+Pension\s+Fund|Norwegian\s+Armed\s+Forces|"
    r"Forsvaret|Forsvarsmateriell|Fornsvarsmateriell)", re.I)

SOFT = re.compile(r"(is\s+an?\s+advantage|an?\s+advantage|nice\s+to\s+have|is\s+a\s+(?:plus|bonus)|"
                   r"preferred|desirable|optional|but\s+not\s+a\s+requirement|er\s+et\s+pluss|"
                   r"pluss\s+til|er\s+en\s+fordel|consider(?:ed)?\s+an?\s+advantage|"
                   r"see\s+as\s+a\s+(?:bonus|plus)|is\s+a\s+plus|or\s+a\s+plus|"
                   r"an?\s+other\s+European\s+languages?\s+are\s+a\s+plus|"
                   r"would\s+be\s+(?:an?\s+)?(?:advantage|plus)|not\s+a\s+requirement|"
                   r"er\s+et\s+pluss|fordel)", re.I)

def windows(text, pat, w=150):
    out = []
    rx = pat if hasattr(pat, "finditer") else re.compile(pat, re.I)
    for m in rx.finditer(text):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def lang_hard_hits(body):
    hits = []
    for w in windows(body, LANG_CTX):
        if INCIDENTAL.search(w) and not re.search(
                r"(norsk|norwegian|skandinav\w*|scandinav\w*|nordisk)[^.]{0,40}"
                r"(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|skriver|krav|påkrevd|"
                r"arbeidsspråk|working\s+language)", w, re.I):
            continue
        if SOFT.search(w) and not re.search(r"(er\s+et\s+krav|krav|påkrevd|required|must\s+have|"
                                            r"må\s+(?:kunne|beherske|snakke)|working\s+language\s+will|"
                                            r"everyday\s+working\s+language|daily\s+working\s+language|"
                                            r"er\s+ditt\s+arbeidsspråk)", w, re.I):
            continue
        hits.append(w)
    return list(dict.fromkeys(hits))

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    review = json.load(open(f"{WORKDIR}/finn_review.json"))
    miss = json.load(open(f"{WORKDIR}/finn_missing_lang.json"))
    ids = []
    for r in review + miss:
        if r["id"] not in ids:
            ids.append(r["id"])
    out = []
    for i in ids:
        d = det[i]
        body = d.get("body","")
        hits = lang_hard_hits(body)
        out.append({"id": i, "url": d["url"], "title": d.get("title",""), "company": d.get("company",""),
                    "location": d.get("location",""), "date": d.get("date","")[:10],
                    "wl": d.get("info",{}).get("Arbeidsspråk",""), "hits": hits,
                    "body_len": len(body)})
    json.dump(out, open(f"{WORKDIR}/finn_hits_all.json","w"), ensure_ascii=False, indent=1)
    clean = [r for r in out if not r["hits"]]
    print("candidates scanned:", len(out), "| no Norwegian-language requirement found:", len(clean))
    for r in sorted(clean, key=lambda x: x["date"], reverse=True):
        print(f"{r['date']} | {r['title'][:64]:64} | {r['company'][:22]:22} | wl={r['wl'][:16]:16} | {r['id']}")
    json.dump(clean, open(f"{WORKDIR}/finn_no_no_req.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
