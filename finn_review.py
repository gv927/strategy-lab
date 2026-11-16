#!/usr/bin/env python3
"""Build review list: English-dominant title-matched ads, with language context windows."""
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
    r"offshore|maritime|heritage)", re.I)

def other_windows(body):
    res = []
    for p in fl2.OTHER_LANG:
        res += fl2.windows(body, p, 120)
    return res

def main():
    short = json.load(open(f"{WORKDIR}/finn_title_short.json"))
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    out = []
    for r in short:
        body = r.get("body") or det[r["id"]]["body"]
        bb = fl.body_only(body)
        en = len(re.findall(fl.EN_STOP, bb, re.I))
        nor = len(re.findall(fl.NOR_STOP, bb, re.I))
        ratio = en / max(1, en + nor)
        if ratio < 0.68:
            continue
        hard, soft = fl2.classify_norwegian(body)
        hard_l = [w for w in hard if not NATIONALITY.search(w)]
        soft_l = [w for w in soft if not NATIONALITY.search(w)]
        out.append({**{k: r[k] for k in ("id", "url", "title", "company", "location", "date")},
                    "wl": r["wl"], "cats": r["cats"], "exp": r["exp"], "senior": r["senior"],
                    "ratio": round(ratio, 3), "hard": hard_l, "soft": soft_l,
                    "other": other_windows(body)})
    out.sort(key=lambda x: x["date"], reverse=True)
    print("English-dominant title-matched:", len(out))
    for r in out:
        flag = ("HARD" if r["hard"] else "") + (" soft" if r["soft"] else "")
        print(f"{r['date'][:10]} | {r['title'][:62]:62} | {r['company'][:20]:20} | "
              f"wl={r['wl'][:14]:14} | rt={r['ratio']:.2f} | exp={r['exp']} | "
              f"{'/'.join(r['cats'])[:24]:24} | {flag}")
    json.dump(out, open(f"{WORKDIR}/finn_review.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
