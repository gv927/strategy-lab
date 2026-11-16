#!/usr/bin/env python3
"""Apply finn_lang3 gate + profile filter over the full Oslo candidate pool."""
import json, re, sys, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("l3", "/home/ubuntu/finn_lang3.py")
l3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3)

TARGET = {
    "banking/financial services": r"\b(bank|financ|credit|loan|mortgage|treasury|wealth|fund|"
        r"invest|insurance|broker|payment|risk|compliance|aml|kyc|accounting|accountant|"
        r"controller|audit|equity|capital\s+market|regnskap|økonom|budsjett|regulatory|"
        r"underwrit\w*|claims|policy|actuar\w*)\b",
    "customer service/sales/support": r"\b(customer|sales|salg|service|support|advisor|adviser|"
        r"kunde|konsulent|account\s+(?:manager|executive)|business\s+development|"
        r"business\s+partner|key\s+account|sales\s+advisor|store\s+associate|shop\s+assistant|"
        r"retail|commercial|account\s+executive|sales\s+executive|demand\s+generation|"
        r"partnership\w*|commercial)\b",
    "administration/office": r"\b(administra|office|assistant|coordinator|reception|"
        r"kontor|sekretær|document\s+controller|back\s*office|saksbehandler)\b",
    "marketing/communication": r"\b(market|markedsfør|brand|campaign|content|growth|demand\s+gen|"
        r"social\s+media|seo|digital\s+market|performance\s+market|communications?|"
        r"copywriter|creative|communications)\b",
    "entry-level tech/IT": r"\b(junior|graduate|trainee|intern|entry\s+level|associate|"
        r"business\s+applications|it\s+support|service\s+desk|help\s*desk|user\s+support)\b",
}
SENIOR = re.compile(r"\b(chief|ceo|cfo|cto|coo|cmo|ciso|head\s+of|director|vp|vice\s+president|"
                     r"general\s+manager)\b", re.I)
OFF_PROFILE = re.compile(r"\b(engineer|engineering|developer|software|architect|mechanical|"
    r"electrical|hvac|technician|nurse|sykepleier|doctor|laboratory|pharmacist|"
    r"driver|chauffeur|servicetekniker|kokk|cook|chef|housekeeping|installer|"
    r"montasje|stiknings|planner|teacher|lærer|barnehage|cyber|devsecops|"
    r"data\s+(?:engineer|analyst|scientist)|fullstack|frontend|backend|embedded|qa/qc|"
    r"quality\s+assurance|hse\b|product\s+manager|product\s+owner|"
    r"engineering\s+manager|project\s+manager|procurement|maintenance|"
    r"package\s+manager|process\s+engineer|legal\s+advisor|jurist|"
    r"attorney|professor|political\s+and\s+economic|system\s+manager|"
    r"release\s+manager|data\s+solutions|chief\s+technology)\b", re.I)

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    # candidate pool = all Oslo ads whose body is English-dominant (from earlier triage)
    pool = json.load(open(f"{WORKDIR}/finn_review.json")) + json.load(open(f"{WORKDIR}/finn_missing_lang.json"))
    seen = set(); rows = []
    for r in pool:
        if r["id"] in seen: continue
        seen.add(r["id"])
        d = det[r["id"]]
        body = d.get("body", "")
        hard, soft = l3.evaluate(body)
        title = d.get("title", "")
        cats = [k for k, p in TARGET.items() if re.search(p, f"{title}\n{body}", re.I)]
        rows.append({"id": r["id"], "url": d["url"], "title": title, "company": d.get("company",""),
                     "location": d.get("location",""), "date": d.get("date","")[:10],
                     "wl": d.get("info",{}).get("Arbeidsspråk",""), "cats": cats,
                     "off": bool(OFF_PROFILE.search(title)), "senior": bool(SENIOR.search(title)),
                     "hard": hard, "soft": soft})
    json.dump(rows, open(f"{WORKDIR}/finn_gate3.json","w"), ensure_ascii=False, indent=1)
    clean = [r for r in rows if not r["hard"]]
    keep = [r for r in clean if r["cats"] and not r["off"] and not r["senior"]]
    print(f"pool={len(rows)} | no-Norwegian-requirement={len(clean)} | +profile+seniority={len(keep)}\n")
    for r in sorted(keep, key=lambda x: x["date"], reverse=True):
        s = " [NO=advantage only]" if r["soft"] else ""
        print(f"{r['date']} | {r['title'][:66]}\n      {r['company'][:26]:26} | {r['location'][:24]:24} | wl={r['wl'][:16]:16} | {r['id']}{s}\n      cats: {', '.join(r['cats'])}")
    json.dump(keep, open(f"{WORKDIR}/finn_gate3_pass.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
