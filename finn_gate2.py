#!/usr/bin/env python3
"""Language-aware soft/hard cancel + role-profile filter. Final shortlist generator."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

LANG_TOKEN = re.compile(r"\b(norsk|norwegian|engelsk|english|fransk|french|tysk|german|italiensk|italian|"
                         r"svensk|swedish|dansk|danish|spansk|spanish|arabisk|arabic|portugisisk|"
                         r"polsk|polish|nederlandsk|dutch|mandarin|kinesisk|chinese|hindi|"
                         r"scandinavian|skandinavisk|nordisk|nordic)\b", re.I)

HARD_CUE = [
    r"fluen\w*\s+(?:i\s+)?norsk", r"fluen\w*\s+(?:i\s+)?norwegian", r"norsk\w*\s+og\s+engelsk",
    r"norsk\w*\s+eller\s+engelsk", r"norsk\w*\s+som\s+arbeidsspråk", r"norsk\s+er\s+arbeidsspråk",
    r"norsk[^.]{0,45}(?:språk|beherskes|må\s+kunne|må\s+beherske|er\s+et\s+krav|er\s+krav|påkrevd|"
    r"krav|grunnleggende\s+norsk)", r"norsk[^.]{0,30}(?:proficien\w*|språkkunnskap|ferdighet\w*)",
    r"(?:good|strong|excellent|solid)\s+(?:command|knowledge|proficiency|skills)[^.]{0,35}norsk",
    r"norsk[^.]{0,35}(?:språklig|grammatikk|forstår\w*)",
    r"norwegian\s+language\s+skills", r"norwegian\s+on\s+a\s+fluent", r"norwegian\s+fluen\w*",
    r"norwegian\s+proficien\w*", r"working\s+language\s+will\s+be\s+norwegian",
    r"everyday\s+working\s+language", r"arbeidsspråk[^.]{0,30}norsk", r"norsk[^.]{0,30}arbeidsspråk",
    r"behersk\w*[^.]{0,30}norsk", r"snakker[^.]{0,25}norsk", r"skriver[^.]{0,25}norsk",
    r"skandinavis\w*\s+(?:språk|language)", r"ett\s+skandinavisk", r"et\s+skandinavisk",
    r"nordisk\s+språk", r"(?:a\s+)?scandinavian\s+language",
    r"norsk[^.]{0,25}\band\s+english", r"english\s+and\s+norsk",
    r"norsk[^.]{0,40}\bog\s+engelsk", r"god\s+norsk", r"gode\s+norsk",
    r"norsk[^.]{0,30}nivå", r"norsk[^.]{0,30}må\s+beherskes", r"norsk[^.]{0,20}\bis\s+(?:et\s+)?krav",
    r"norsk\w*\s+og\s+engelsk,?\s+(?:både|muntlig|skriftlig)",
]
SOFT_MARK = re.compile(r"(er\s+en\s+fordel|er\s+et\s+pluss|pluss\s+til|fordel|an\s+advantage|"
                        r"is\s+an?\s+advantage|is\s+a\s+plus|nice\s+to\s+have|optional|preferred|"
                        r"er\s+ønskelig|will\s+be\s+considered\s+an\s+advantage|"
                        r"but\s+not\s+a\s+requirement|er\s+en\s+bonus)", re.I)

def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n", text)
    return [" ".join(p.split()) for p in parts if p.strip()]

def evaluate(body):
    """Return (hard_hits, soft_hits) language cues about Norwegian."""
    hard, soft = [], []
    for sent in sentences(body):
        low = sent.lower()
        if not re.search(r"\b(norsk|norwegian|scandinav\w*|skandinav\w*|nordisk|nordic)\b", low):
            continue
        m = None
        for p in HARD_CUE:
            mm = re.search(p, sent, re.I)
            if mm:
                m = mm
                break
        if not m:
            continue
        # does a soft marker qualify the Norwegian mention specifically?
        # check the text between the Norwegian mention and the soft marker
        nor_pos = [mm.start() for mm in re.finditer(r"\b(norsk|norwegian)\b", sent, re.I)]
        soft_pos = [mm.start() for mm in SOFT_MARK.finditer(sent)]
        other_lang_between = False
        for sm in soft_pos:
            for np_ in nor_pos:
                lo, hi = min(np_, sm), max(np_, sm)
                between = sent[lo:hi]
                toks = [t for t in LANG_TOKEN.findall(between) if t.lower() not in ("norsk", "norwegian")]
                if toks:
                    other_lang_between = True
        if soft_pos and not other_lang_between:
            soft.append(sent)
        else:
            hard.append(sent)
    return hard, soft

# ---- role profile filter ----
TARGET = {
    "banking/financial services": r"\b(bank|financ|credit|loan|mortgage|treasury|wealth|fund|"
        r"invest|insurance|broker|payment|risk|compliance|aml|kyc|accounting|accountant|"
        r"controller|audit|equity|capital\s+market|regnskap|økonom|budsjett)\b",
    "customer service/sales/support": r"\b(customer|sales|salg|service|support|advisor|adviser|"
        r"kunde|konsulent|account\s+(?:manager|executive)|business\s+development|"
        r"business\s+partner|key\s+account|sales\s+advisor|store\s+associate|shop\s+assistant|"
        r"retail|commercial|account\s+executive)\b",
    "administration/office": r"\b(administra|office|assistant|coordinator|reception|"
        r"kontor|sekretær|document\s+controller|back\s*office|saksbehandler)\b",
    "marketing/communication": r"\b(market|markedsfør|brand|campaign|content|growth|demand\s+gen|"
        r"social\s+media|seo|digital\s+market|performance\s+market|communications?|"
        r"copywriter|creative)\b",
    "entry-level tech/IT": r"\b(junior|graduate|trainee|intern|entry\s+level|associate|"
        r"business\s+applications|it\s+support|service\s+desk|help\s*desk|user\s+support)\b",
}
SENIOR = re.compile(r"\b(chief|ceo|cfo|cto|coo|cmo|ciso|head\s+of|director|vp|vice\s+president|"
                     r"general\s+manager|general\s+director)\b", re.I)
OFF_PROFILE = re.compile(r"\b(engineer|engineering|developer|software|architect|mechanical|"
    r"electrical|hvac|technician|nurse|sykepleier|doctor|lab\s|scientist|laboratory|"
    r"driver|chauffeur|servicetekniker|kokk|cook|chef|waitress|housekeeping|installer|"
    r"montasje|stiknings|planner|plann|teacher|lærer|barnehage|cyber|security\s+(?:lead|architect|"
    r"specialist)|devsecops|data\s+(?:engineer|analyst|scientist)|fullstack|frontend|backend|"
    r"embedded|qa/qc|quality\s+assurance|hse\b|product\s+manager|product\s+owner|"
    r"operations\s+manager|engineering\s+manager|project\s+manager|procurement|maintenance|"
    r"compliance\s+lead|package\s+manager|process\s+engineer|legal\s+advisor|jurist|"
    r"attorney|professor|policy\s+officer|political\s+and\s+economic)\b", re.I)

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    pool = json.load(open(f"{WORKDIR}/finn_review.json")) + json.load(open(f"{WORKDIR}/finn_missing_lang.json"))
    seen = set(); rows = []
    for r in pool:
        if r["id"] in seen: continue
        seen.add(r["id"])
        d = det[r["id"]]
        body = d.get("body", "")
        hard, soft = evaluate(body)
        title = d.get("title", "")
        cats = [k for k, p in TARGET.items() if re.search(p, f"{title}\n{body}", re.I)]
        off = bool(OFF_PROFILE.search(title))
        senior = bool(SENIOR.search(title))
        rows.append({"id": r["id"], "url": d["url"], "title": title, "company": d.get("company",""),
                     "location": d.get("location",""), "date": d.get("date","")[:10],
                     "wl": d.get("info",{}).get("Arbeidsspråk",""), "cats": cats,
                     "off": off, "senior": senior, "hard": hard, "soft": soft})
    json.dump(rows, open(f"{WORKDIR}/finn_gate2.json","w"), ensure_ascii=False, indent=1)
    keep = [r for r in rows if not r["hard"] and r["cats"] and not r["off"] and not r["senior"]]
    print(f"pool={len(rows)} | pass language+profile+seniority: {len(keep)}")
    print()
    for r in sorted(keep, key=lambda x: x["date"], reverse=True):
        soft = " (Norwegian listed as advantage only)" if r["soft"] else ""
        print(f"{r['date']} | {r['title'][:64]:64}\n      {r['company'][:26]:26} | {r['location'][:22]:22} | wl={r['wl'][:16]:16} | {r['id']}{soft}")
    json.dump(keep, open(f"{WORKDIR}/finn_gate2_pass.json","w"), ensure_ascii=False, indent=1)
    print()
    print("=== excluded by profile/seniority (language-clean) ===")
    for r in rows:
        if not r["hard"] and (r["off"] or r["senior"]) and r["cats"]:
            print(f"  {'OFF' if r['off'] else 'SENIOR'} | {r['title'][:66]} | {r['company'][:22]} | {r['id']}")

if __name__ == "__main__":
    main()
