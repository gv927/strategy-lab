#!/usr/bin/env python3
"""Tighter pipeline: title-level role match + English + no-Norwegian + seniority."""
import json, re, sys

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

# --- role match on TITLE (and short head of body) ---
TITLE_TARGETS = {
 "banking/financial services": [
   r"\bbank", r"\bfinanc", r"\bcredit\b", r"\bloan", r"\bmortgage", r"\btreasury",
   r"\bwealth", r"\basset\s+manager", r"\bfund\b", r"\brisk\b", r"\bcompliance\b",
   r"\baml\b", r"\bkyc\b", r"\binsurance", r"\bbroker", r"\bpayment", r"\binvest",
   r"\baccountant\b", r"\bcontroller\b", r"\bbookkeep", r"\baudit", r"\bøkonom",
   r"\bregnskap", r"\bfinancial\s+(?:analyst|controller|controller|advisor|adviser)",
 ],
 "customer service / support": [
   r"\bcustomer\s+(?:service|support|care|success|advisor|adviser|experience|relation)",
   r"\bservice\s+(?:manager|advisor|consultant|specialist|representative)",
   r"\bsupport\s+(?:agent|specialist|manager|consultant|advisor)",
   r"\bcontact\s+center", r"\bhelp\s*desk", r"\bcall\s*center", r"\brelationship\s+manager",
   r"\bkunde", r"\bservice", r"\bsupport",
 ],
 "sales / commercial": [
   r"\bsales", r"\bsalg", r"\bsell", r"\brevenue", r"\bcommercial", r"\baccount\s+(?:manager|executive)",
   r"\bbusiness\s+development", r"\bbusiness\s+partner", r"\bkey\s+account",
   r"\blead\s+generation", r"\binside\s+sales", r"\bsales\s+manager",
 ],
 "administration / office": [
   r"\badministrat", r"\boffice\s+(?:manager|assistant|admin|coordinator)",
   r"\bexecutive\s+assistant", r"\bpersonal\s+assistant", r"\badministrative",
   r"\bback\s*office", r"\bdocument\s+controller", r"\breceptionist", r"\bkontor",
   r"\bsaksbehandler", r"\bkoordinator", r"\bassistant",
 ],
 "marketing / communication": [
   r"\bmarket", r"\bmarkedsføring", r"\bbrand", r"\bcampaign", r"\bcontent\s+(?:manager|producer|strategist)",
   r"\bsocial\s+media", r"\bseo\b", r"\bsem\b", r"\bgrowth\s+market", r"\bperformance\s+market",
   r"\bmarketing\s+consultant", r"\bdigital\s+market",
 ],
 "entry-level tech / IT support": [
   r"\bhelp\s*desk\s+(?:support|technician)", r"\bitsupport", r"\bservice\s+desk",
   r"\bsupport\s+technician", r"\bjunior\s+(?:developer|analyst|consultant|advisor|specialist)",
   r"\bintern\b", r"\btrainee", r"\bgraduate\b", r"\bentry\s+level", r"\bassociate\b",
 ],
}
# titles that are clearly NOT the target domains (exclude engineers/IT dev heavy roles)
TITLE_EXCLUDE = re.compile(
 r"\bengineer|engineering|developer|programmer|software|architect|technician|technologist|"
 r"\bdevops|installer|installers|montasje|mekaniker|mechanical|electrical|hvac|"
 r"\bnurse|sykepleier|doctor|helsepersonell|lab\b|laboratory|scientist|pharmacist|"
 r"\bdriver|chauffeur|drosje|bilmekaniker|sjåfør|kokk|cook|chef|waiter|serverings|"
 r"\bsmør\b|barista|housekeeping|renholder|hjelpetrener|fagperson|"
 r"\bproject\s+planner|planner\b|construction|construction|bygg|anlegg|"
 r"\bhelse|sykehus|hospital|teacher|lærer|undervisning|barnehage|"
 r"\bcyber|security\s+(?:lead|architect|specialist|engineer)|devsecops|"
 r"\bdata\s+(?:engineer|analyst|scientist)|fullstack|frontend|backend|embedded|"
 r"\bqa/qc|quality\s+assurance|hse\b|health\s+safety|environment", re.I)

SENIOR_TITLE = re.compile(r"\b(chief|ceo|cfo|cto|coo|cmo|ciso|head\s+of|director|"
                           r"vice\s+president|general\s+manager|plant\s+manager|"
                           r"engineering\s+manager|senior\s+manager)\b", re.I)
SENIOR_BODY = [
    r"\b(?:minimum\s+)?(?:of\s+)?(\d{2})\s*\+?\s*(?:års\s+)?(?:relevant\s+)?(?:erfarenhet|years of experience)",
    r"\b(\d{2})\s*\+?\s*(?:års|years)\b",
    r"\bminimum\s+(\d{2})\s*\+?\s*years",
    r"\b(?:at\s+least|more\s+than)\s+(\d{2})\s*\+?\s*years",
    r"\b(?:master'?s|master)\s+(?:degree|level)\b[^.\n]{0,60}(?:required|er\s+påkrevd|krav)",
    r"\b5\s*\+?\s*years\b", r"\b7\s*\+?\s*years\b", r"\b10\s*\+?\s*years\b",
]
EXPERIENCE_OK = re.compile(r"\b(\d)\s*\+?\s*(?:years|år)\b")

def windows(text, pat, w=130):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def main():
    det = json.load(open(f"{WORKDIR}/finn_details_all.json"))
    out = []
    for d in det:
        title = d.get("title","") or ""
        body = d.get("body","")
        info = d.get("info",{}) or {}
        wl = ""
        for k,v in info.items():
            if "arbeidsspr" in k.lower(): wl = v
        cats = [k for k, pats in TITLE_TARGETS.items()
                if any(re.search(p, title, re.I) for p in pats)]
        excluded = bool(TITLE_EXCLUDE.search(title))
        # experience requirement mentioned in the body near 'years of experience'
        exp = []
        for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:years|år)\s+(?:of\s+)?(?:relevant\s+)?(?:experience|erfaring)", body, re.I):
            exp.append(int(m.group(1)))
        senior = bool(SENIOR_TITLE.search(title)) or any(e >= 8 for e in exp)
        out.append({**{k:d.get(k) for k in ("id","url","title","company","location","date")},
                    "wl": wl, "cats": cats, "excluded": excluded, "exp": exp,
                    "senior": senior, "body": body, "body_len": d.get("body_len",0)})
    json.dump(out, open(f"{WORKDIR}/finn_titles.json","w"), ensure_ascii=False, indent=1)
    short = [r for r in out if r["cats"] and not r["excluded"]]
    print("total", len(out), "| title-matched & not excluded:", len(short))
    for r in sorted(short, key=lambda x: x["date"], reverse=True):
        print(f"{r['date'][:10]} | {r['title'][:66]:66} | {r['company'][:22]:22} | wl={r['wl'][:14]:14} | exp={r['exp']} | {'/'.join(r['cats'])[:34]}")
    json.dump(short, open(f"{WORKDIR}/finn_title_short.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
