#!/usr/bin/env python3
"""Context-aware language check: distinguish Norwegian REQUIREMENT vs mere advantage."""
import json, re, sys

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

# Any mention of Norwegian / Norwegian-language ability
NOR_MENTION = r"(norsk|norwegian|norsktalende|norsktalende|skandinav\w*|nordisk\s+språk|scandinavian\s+language)"
# Phrases that mark the mention as soft/optional
SOFT = re.compile(r"(is\s+an?\s+advantage|an?\s+advantage|nice\s+to\s+have|is\s+a\s+(?:plus|bonus)|"
                   r"preferred|desirable|optional|would\s+be\s+(?:an?\s+)?(?:advantage|plus)|"
                   r"er\s+et\s+(?:pluss|fordel)|pluss\s+til|ønskelig|foretrekkes|"
                   r"good\s+to\s+have|asset\b|merit|an\s+asset|bonus)", re.I)
# Phrases that mark it as a hard requirement (used for emphasis)
HARD = re.compile(r"(required|must\s+(?:speak|have|be\s+fluent|master)|requirement|essential|"
                   r"krav|påkrevd|må\s+(?:kunne|beherske|snakke)|forutsetter|"
                   r"you\s+must|we\s+require|it\s+is\s+essential|only\s+consider\s+candidates)", re.I)

# Norwegian-specific wording patterns (independent of 'norsk' token)
NOR_SPECIFIC = [
    r"flytende\s+(?:i\s+)?norsk", r"norsk\s+flytende", r"norsktalende", r"norsk\s+talende",
    r"snakker\s+og\s+skriver\s+norsk", r"du\s+snakker\s+norsk", r"behandler\s+norsk", r"skriver\s+norsk",
    r"god\s+i\s+norsk", r"gode\s+norsk", r"gods\s+norsk", r"norsk\s+ferdigheter",
    r"norsk\s+forståelse", r"forståelse\s+av\s+norsk", r"norsk\s+språklig",
    r"skriftlig\w*[^.\n]{0,50}norsk", r"norsk[^.\n]{0,50}(?:språklig|grammatikk)",
    r"arbeidsspråk[^.\n]{0,40}norsk", r"norsk[^.\n]{0,40}arbeidsspråk",
    r"språk[^.\n]{0,60}norsk", r"norsk[^.\n]{0,60}språk",
    r"norsk\w*\s+som\s+arbeidsspråk", r"norsk\s+er\s+arbeidsspråk",
    r"skandinavis\w*\s+(?:språk|language)", r"ett\s+skandinavisk", r"et\s+skandinavisk",
    r"nordisk\s+språk", r"scandinavian\s+language", r"nordic\s+language",
    r"norsk[^.\n]{0,30}(?:er\s+et\s+krav|påkrevd)", r"norsk[^.\n]{0,70}(?:krav|påkrevd|required)",
    r"krav[^.\n]{0,70}norsk", r"norsk\s+språkkunnskap", r"erfarenhet\s+med\s+norsk",
    r"like\s+trygg\s+på\s+norsk", r"hva\s+vi\s+tilbyr",
]
OTHER_LANG = [
    r"sprichst\s+du\s+deutsch", r"german\s+language", r"kenntnisse\w*\s+deutsch",
    r"fransk[^.\n]{0,25}(?:språk|krav)", r"french\s+language", r"svenska?\s+flytende",
    r"italiensk[^.\n]{0,20}krav", r"italian\s+language", r"polsk[^.\n]{0,20}(?:språk|krav)",
]

def windows(text, pat, w=150):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def classify_norwegian(body):
    """Return (hard_hits, soft_hits) windows mentioning Norwegian language."""
    hard, soft = [], []
    for w in windows(body, NOR_MENTION):
        if SOFT.search(w):
            soft.append(w)
        else:
            hard.append(w)
    for p in NOR_SPECIFIC:
        for w in windows(body, p):
            # 'hva vi tilbyr' etc are UI labels - skip
            if re.search(r"hva\s+vi\s+tilbyr", w, re.I) and not re.search(r"norsk", w, re.I):
                continue
            hard.append(w)
    # dedupe
    hard = list(dict.fromkeys(hard)); soft = list(dict.fromkeys(soft))
    # a soft window that also contains a hard cue -> hard
    final_hard = []
    for w in hard:
        final_hard.append(w)
    for w in soft:
        if HARD.search(w) and not SOFT.search(w):
            final_hard.append(w)
    return list(dict.fromkeys(final_hard)), [w for w in soft if w not in final_hard]

def main():
    short = json.load(open(f"{WORKDIR}/finn_title_short.json"))
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    rows = []
    for r in short:
        body = r.get("body","")
        hard, soft = classify_norwegian(body)
        other = []
        for p in OTHER_LANG:
            other += windows(body, p)
        rows.append({**{k:r[k] for k in ("id","url","title","company","location","date")},
                     "wl": r["wl"], "cats": r["cats"], "exp": r["exp"], "senior": r["senior"],
                     "hard": hard, "soft": soft, "other": other})
    json.dump(rows, open(f"{WORKDIR}/finn_lang2.json","w"), ensure_ascii=False, indent=1)
    ok = [r for r in rows if not r["hard"] and not r["other"]]
    print("title-matched:", len(rows), "| no hard Norwegian requirement:", len(ok))
    for r in sorted(ok, key=lambda x: x["date"], reverse=True):
        flag = "SOFT:" + str(len(r["soft"])) if r["soft"] else ""
        print(f"{r['date'][:10]} | {r['title'][:64]:64} | {r['company'][:22]:22} | wl={r['wl'][:16]:16} | exp={r['exp']} | {'/'.join(r['cats'])[:28]:28} | {flag}")
    json.dump(ok, open(f"{WORKDIR}/finn_lang2_ok.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
