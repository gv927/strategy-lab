#!/usr/bin/env python3
"""Apply language triage to the additional English-title ads not caught by title matching."""
import json, re, sys, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("fl", "/home/ubuntu/finn_lang.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)
spec2 = importlib.util.spec_from_file_location("fl2", "/home/ubuntu/finn_lang2.py")
fl2 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(fl2)

NATIONALITY = re.compile(
    r"Norwegian\s+(company|scale-?up|business|market|industry|sector|subsidiar\w+|branch\w*|"
    r"offices?|law|act|court\w*|authorit\w+|embassy|government|culture|society|kroner|currency|"
    r"tax|working\s+hours|public|state|municipality|heritage|maintenance|merchant|energy|"
    r"offshore|maritime|defence|defense|security)", re.I)

def other_windows(body):
    res = []
    for p in fl2.OTHER_LANG:
        res += fl2.windows(body, p, 120)
    return res

def main():
    det = json.load(open(f"{WORKDIR}/finn_details_all.json"))
    short_ids = {r["id"] for r in json.load(open(f"{WORKDIR}/finn_title_short.json"))}
    NOR_CHARS = re.compile(r"[æøåÆØÅ]")
    KEY = re.compile(r"\b(bank|financ|sales|sell|mark|customer|service|support|account|advisor|adviser|"
                      r"consultant|manager|analyst|officer|assistant|coordinator|specialist|associate|"
                      r"executive|representative|credit|risk|compliance|treasury|insurance|"
                      r"payment|wealth|fund|investment|broker|admin|office|reception|store|shop|"
                      r"business|growth|content|brand|digital|web|social|demand|trade|underwrit)\b", re.I)
    rows = []
    for d in det:
        t = d.get("title","") or ""
        if d["id"] in short_ids: continue
        if NOR_CHARS.search(t): continue
        if not KEY.search(t): continue
        body = d.get("body","")
        if len(body) < 400: continue
        bb = fl.body_only(body)
        en = len(re.findall(fl.EN_STOP, bb, re.I))
        nor = len(re.findall(fl.NOR_STOP, bb, re.I))
        ratio = en / max(1, en + nor)
        hard, soft = fl2.classify_norwegian(body)
        hard_l = [w for w in hard if not NATIONALITY.search(w)]
        soft_l = [w for w in soft if not NATIONALITY.search(w)]
        rows.append({"id": d["id"], "url": d["url"], "title": t, "company": d.get("company",""),
                     "location": d.get("location",""), "date": d.get("date","")[:10],
                     "wl": d.get("info",{}).get("Arbeidsspråk",""), "ratio": round(ratio,3),
                     "hard": hard_l, "soft": soft_l, "other": other_windows(body)})
    rows.sort(key=lambda x: x["date"], reverse=True)
    for r in rows:
        flag = ("HARD" if r["hard"] else "") + (" soft" if r["soft"] else "")
        print(f"{r['date']} | {r['title'][:66]:66} | {r['company'][:20]:20} | wl={r['wl'][:16]:16} | rt={r['ratio']:.2f} | {flag}")
    json.dump(rows, open(f"{WORKDIR}/finn_missing_lang.json","w"), ensure_ascii=False, indent=1)
    clean = [r for r in rows if not r["hard"] and not r["other"] and r["ratio"] >= 0.68]
    print("\nCLEAN additional:", len(clean))
    for r in clean:
        print(f"  {r['date']} | {r['title'][:60]} | {r['company']} | {r['url']}")

if __name__ == "__main__":
    main()
