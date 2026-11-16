#!/usr/bin/env python3
"""Final triage: classify each Norwegian mention as language-requirement vs incidental."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

# mentions of Norwegian that are NOT about language ability
INCIDENTAL = re.compile(
    r"(Norwegian\s+(public\s+service|defence|defense|armed\s+forces|government|state|municipality|"
    r"company|companies|business|scale-?up|market|markets|industry|sector|customer|customers|"
    r"office|offices|branch|subsidiary|subsidiar\w+|economy|krone|kroner|currency|law|laws|"
    r"act|regulation\w*|authorit\w+|court\w*|embassy|consulate|heritage|culture|society|"
    r"tax|security\s+act|public\s+administration\s+act|bar|attorney|work\s+environment|"
    r"working\s+hours|public\s+holiday\w*|territory|waters|sea|coast|offshore|maritime|"
    r"maintenance|merchant|energy|telecom\w*|airline\w*|bank\w*|finance|financial|"
    r"pension\s+fund|insurance|ship|shipping|forestry|fish|fisher\w*|agricultur\w+|"
    r"construction|standards|practice|practices|residents?|nationality|citizenship)|"
    r"Norwegian\s+Security\s+Act|Norsk\s+(titanium|hydro|data|butikk|industri|luftfart|"
    r"verksted|bil|miljø|teknologi|bane|helse|vare|butikk|bank|finans)|"
    r"Norwegian\s+and\s+(?:Nordic|Scandinavian)\b|"
    r"Norwegian\s+and\s+English\s+(?:company|market|offices?)|"
    r"in\s+the\s+Norwegian\s+market|Norwegian\s+offices|Norwegian\s+company|"
    r"Norwegian\s+Public\s+Service\s+Pension\s+Fund|Norwegian\s+Armed\s+Forces|"
    r"Forsvaret|Forsvarsmateriell)", re.I)

# language-ability phrasings: the Norwegian word sits near a competence word
LANG_CTX = re.compile(
    r"(norsk|norwegian)[^.]{0,45}(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|"
    r"skriver|forstår\w*|ferdighet\w*|kompetanse|krav|påkrevd|må\s+(?:kunne|beherske|snakke)|"
    r"er\s+et\s+krav|arbeidsspråk|daglig|hverdag)|"
    r"(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|skriver|forstår\w*|"
    r"ferdighet\w*|arbeidsspråk)[^.]{0,45}(norsk|norwegian)|"
    r"(norsk|norwegian)[^.]{0,30}\bog\s+engelsk|norsk\s+og\s+engelsk", re.I)

def windows(text, pat, w=150):
    out = []
    rx = pat if hasattr(pat, "finditer") else re.compile(pat, re.I)
    for m in rx.finditer(text):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def main():
    review = json.load(open(f"{WORKDIR}/finn_review.json"))
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    out = []
    for r in review:
        body = det[r["id"]]["body"]
        lang_wins = windows(body, LANG_CTX)
        # drop windows whose Norwegian mention is purely incidental
        hard = []
        for w in lang_wins:
            if INCIDENTAL.search(w):
                # keep if window ALSO contains an ability word near Norwegian
                if not re.search(r"(norsk|norwegian)[^.]{0,45}(språk|language|fluen\w*|proficien\w*|"
                                 r"behersk\w*|snakker|skriver|krav|påkrevd|arbeidsspråk)", w, re.I):
                    continue
            hard.append(w)
        # Norwegian mentioned at all?
        all_nor = windows(body, r"\b(norsk|norwegian|norsktalende|skandinav\w*|nordisk\s+språk)\b", 60)
        out.append({**r, "lang_hard": hard, "all_nor": all_nor})
    out.sort(key=lambda x: x["date"], reverse=True)
    for r in out:
        flag = "REQ" if r["lang_hard"] else ("nor-mention" if r["all_nor"] else "")
        print(f"{r['date'][:10]} | {r['title'][:60]:60} | {r['company'][:20]:20} | wl={r['wl'][:14]:14} | rt={r['ratio']:.2f} | {flag}")
        for w in r["lang_hard"][:3]:
            print("      HARD>", w[:220])
    json.dump(out, open(f"{WORKDIR}/finn_final_triage.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
