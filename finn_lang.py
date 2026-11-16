#!/usr/bin/env python3
"""Language triage on title-matched Oslo ads: English body, no Norwegian requirement."""
import json, re, sys

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
    r"norsk\w*[^.\n]{0,30}(?:daglig|hverdags)\b",
]
OTHER_REQ = [
    r"sprichst\s+du\s+deutsch", r"german\s+language", r"kenntnisse\w*\s+deutsch",
    r"fransk[^.\n]{0,25}(?:språk|krav)", r"french\s+language", r"svenska?\s+flytende",
    r"italiensk[^.\n]{0,20}krav", r"italian\s+language",
]
EN_STOP = r"\b(the|and|you|your|we|our|will|with|for|are|this|that|from|have|has|not|all)\b"
NOR_STOP = r"\b(og|til|på|med|som|for|er|du|vi|din|dine|det|en|et|har|kan|skal|vil|må|ikke)\b"

def windows(text, pat, w=130):
    out = []
    for m in re.finditer(pat, text, re.I):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(WS_RE.sub(" ", text[a:b].replace("\n"," ")))
    return out

def body_only(body):
    """Strip finn boilerplate (Norwegian UI labels) before language scoring."""
    lines = body.split("\n")
    boiler = {"Kortversjonen","Kvalifikasjoner","Hva vi tilbyr","Er du en god match for denne stillingen?",
              "Vis mindre","Vis hele kortversjonen","Om arbeidsgiveren","Nøkkelord","Spørsmål om stillingen",
              "Firmaets beliggenhet","JobbMatch","Om stillingen","Arbeidsoppgaver","Din bakgrunn og egenskaper",
              "Vi tilbyr","Søknadsfrist","Sektor","Arbeidsspråk","Mulighet for hjemmekontor"}
    return "\n".join(l for l in lines if l.strip() not in boiler)

def main():
    short = json.load(open(f"{WORKDIR}/finn_title_short.json"))
    rows = []
    for r in short:
        body = r.get("body","")
        bb = body_only(body)
        nor_hits = []
        for p in NOR_REQ:
            nor_hits += windows(body, p)
        other_hits = []
        for p in OTHER_REQ:
            other_hits += windows(body, p)
        en = len(re.findall(EN_STOP, bb, re.I))
        nor = len(re.findall(NOR_STOP, bb, re.I))
        ratio = en / max(1, en + nor)
        # explicit English-as-working-language statements
        explicit = []
        for p in [r"working\s+language[^.\n]{0,60}english", r"arbeidsspråk[^.\n]{0,20}engelsk",
                  r"engelsk\s+er\s+arbeidsspråk", r"job\s+language[^.\n]{0,50}english",
                  r"language[^.\n]{0,20}english[^.\n]{0,30}(?:working|requirement)"]:
            explicit += windows(body, p, 100)
        rows.append({**{k:r[k] for k in ("id","url","title","company","location","date")},
                     "wl": r["wl"], "cats": r["cats"], "exp": r["exp"], "senior": r["senior"],
                     "ratio": round(ratio,3), "en": en, "nor": nor,
                     "nor_hits": nor_hits, "other_hits": other_hits, "explicit": explicit})
    json.dump(rows, open(f"{WORKDIR}/finn_lang.json","w"), ensure_ascii=False, indent=1)
    ok = [r for r in rows if not r["nor_hits"] and not r["other_hits"] and r["ratio"] >= 0.70]
    print("title-matched:", len(rows), "| english & no-norwegian:", len(ok))
    print()
    for r in sorted(ok, key=lambda x: x["date"], reverse=True):
        print(f"{r['date'][:10]} | {r['title'][:62]:62} | {r['company'][:22]:22} | wl={r['wl'][:16]:16} | ratio={r['ratio']:.2f} | exp={r['exp']} | {'/'.join(r['cats'])[:30]}")
    json.dump(ok, open(f"{WORKDIR}/finn_lang_ok.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
