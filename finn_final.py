#!/usr/bin/env python3
"""Final pipeline: relevance -> English -> no-Norwegian -> seniority match."""
import json, re, sys, collections

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

NOR_REQ = [
    r"flytende\s+(?:i\s+)?norsk", r"norsk\s+flytende", r"fluen\w*\s+(?:i|in)\s+norwegian",
    r"norwegian\s+fluen\w*", r"god\s+i\s+norsk", r"gode\s+norsk", r"gods\s+norsk",
    r"good\s+norwegian", r"proficien\w*\s+in\s+norwegian", r"norwegian\s+proficien\w*",
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
    r"norsk[^.\n]{0,40}(?:språklig|grammatikk)", r"norsk\s+språklig",
]
OTHER_REQ = [
    r"sprichst\s+du\s+deutsch", r"german\s+language", r"kenntnisse\w*\s+deutsch",
    r"fransk[^.\n]{0,25}(?:språk|krav)", r"french\s+language", r"svenska?\s+flytende",
    r"italiensk[^.\n]{0,20}krav", r"italian\s+language",
]

# Target-domain relevance (title + body)
DOMAIN_PATTERNS = {
  "banking/financial": r"\b(bank|banking|banker|finans|financial|finance|credit|loan|mortgage|"
                        r"treasury|investment|investor|wealth|asset\s+manager|fund|risk|compliance|"
                        r"aml|kyc|insurance|pension|broker|payment|capital\s+markets|equity|"
                        r"accounting|accountant|controller|økonom|budsjett|regnskap)\b",
  "sales": r"\b(sales|salg|sell|revenue|commercial|account\s+manager|account\s+executive|"
           r"business\s+development|business\s+partner|key\s+account|kundeansvarlig|kunderådgiver|"
           r"salgskonsulent|salgs|konsulent\s+.*?salg|lead\s+generation|inside\s+sales)\b",
  "customer service": r"\b(customer\s+(?:service|support|care|success|advisor|adviser|relations|"
                     r"experience|loyalty)|kundeservice|kundeseier|kunde(?:service|håndtering|"
                     r"oppfølging)|service\s+(?:manager|advisor|consultant)|support\s+(?:agent|"
                     r"specialist|manager)|contact\s+center|helpdesk)\b",
  "administration": r"\b(administration|administrativ\w*|office\s+(?:manager|assistant|admin)|"
                   r"executive\s+assistant|personal\s+assistant|administrasjon|"
                   r"kontor(?:assistent|leder|administr|medarbeider)|back\s*office|"
                   r"document\s+controller|receptionist|sekretær)\b",
  "marketing": r"\b(marketing|markedsføring|markeds|brand|branding|campaign|content\s+"
               r"(?:manager|strategist|producer)|digital\s+(?:marketing|marketing\s+manager)|"
               r"social\s+media|seo|sem|performance\s+marketing|growth\s+marketing|"
               r"marketing\s+consultant|kommunikasjon|communication)\b",
}
SENIOR_KILL = [
    r"\b(\d{2})\s*\+?\s*(?:års|years)\s+(?:relevant\s+)?(?:erfarenhet|experience)",
    r"\bminimum\s+(?:of\s+)?(\d{2})\s*\+?\s*years",
    r"\b(\d{2})\s*\+?\s*years\b",
    r"\b(ph\.?d|doctorate)\b",
    r"\bhead\s+of\b", r"\bchief\b", r"\bdirector\b", r"\bciso\b", r"\bchief\s+executive\b",
    r"\b(?:minimum|at\s+least)\s+(\d{2})\s*\+?\s*(?:års|years)",
]
SENIOR_TITLE = re.compile(r"\b(chief|ceo|cfo|cto|coo|cmo|ciso|head\s+of|director|vp|vice\s+president|"
                           r"senior\s+manager|general\s+manager|partner)\b", re.I)

def windows(text, pat, w=130):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def classify(d):
    body = d.get("body","")
    title = d.get("title","") or ""
    company = d.get("company","") or ""
    info = d.get("info",{}) or {}
    wl = ""
    for k,v in info.items():
        if "arbeidsspr" in k.lower(): wl = v
    hay = f"{title}\n{company}\n{body}"
    domains = [k for k,p in DOMAIN_PATTERNS.items() if re.search(p, hay, re.I)]
    nor_hits = []
    for p in NOR_REQ:
        nor_hits += windows(body, p)
    other_hits = []
    for p in OTHER_REQ:
        other_hits += windows(body, p)
    # English-ness: ratio of English stopwords vs Norwegian stopwords in body
    en_stop = r"\b(the|and|you|your|we|our|will|with|for|are|this|that|from|have)\b"
    nor_stop = r"\b(og|til|på|med|som|for|er|du|vi|din|det|en|et|har|kan|skal|vil|må|ikke)\b"
    en_cnt = len(re.findall(en_stop, body, re.I))
    nor_cnt = len(re.findall(nor_stop, body, re.I))
    eng_ratio = en_cnt / max(1, en_cnt + nor_cnt)
    sen_hits = []
    for p in SENIOR_KILL:
        for w in windows(body, p, 90):
            sen_hits.append(w)
    return {"id": d["id"], "url": d["url"], "title": title, "company": company,
            "location": d.get("location",""), "date": d.get("date","")[:10], "wl": wl,
            "domains": domains, "nor_hits": nor_hits, "other_hits": other_hits,
            "en_cnt": en_cnt, "nor_cnt": nor_cnt, "eng_ratio": round(eng_ratio,3),
            "senior_hits": sen_hits, "senior_title": bool(SENIOR_TITLE.search(title)),
            "body_len": d.get("body_len",0), "body": body}

def main():
    det = json.load(open(f"{WORKDIR}/finn_details_all.json"))
    rows = [classify(d) for d in det]
    json.dump(rows, open(f"{WORKDIR}/finn_classified.json","w"), ensure_ascii=False, indent=1)
    # Stage 1: domain relevant
    dom = [r for r in rows if r["domains"]]
    # Stage 2: English-language (wl includes Engelsk OR body english-dominant)
    eng = [r for r in dom if ("engelsk" in r["wl"].lower() or r["eng_ratio"] >= 0.62)]
    # Stage 3: no Norwegian requirement
    clean = [r for r in eng if not r["nor_hits"] and not r["other_hits"]]
    # Stage 4: not obviously senior/mismatched
    final = [r for r in clean if not r["senior_title"] and not r["senior_hits"]]
    print(f"total={len(rows)} domain={len(dom)} english={len(eng)} clean={len(clean)} final={len(final)}")
    print()
    for r in sorted(final, key=lambda x: x["date"], reverse=True):
        print(f"{r['date']} | {r['title'][:62]:62} | {r['company'][:24]:24} | {r['wl'][:16]:16} | {','.join(r['domains'])[:38]:38} | er={r['eng_ratio']}")
    json.dump(final, open(f"{WORKDIR}/finn_final.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
