#!/usr/bin/env python3
"""Combine: no hard Norwegian requirement AND English-dominant body."""
import json, re, sys, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("fl", "/home/ubuntu/finn_lang.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)

def main():
    ok2 = json.load(open(f"{WORKDIR}/finn_lang2_ok.json"))
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    rows = []
    for r in ok2:
        body = r.get("body") or det[r["id"]]["body"]
        bb = fl.body_only(body)
        en = len(re.findall(fl.EN_STOP, bb, re.I))
        nor = len(re.findall(fl.NOR_STOP, bb, re.I))
        ratio = en / max(1, en + nor)
        r2 = {**r, "ratio": round(ratio,3), "en": en, "nor": nor}
        rows.append(r2)
    final = [r for r in rows if r["ratio"] >= 0.70]
    print("no-hard-NO:", len(rows), "| + English-dominant:", len(final))
    print()
    for r in sorted(final, key=lambda x: x["date"], reverse=True):
        soft = f"soft={len(r['soft'])}" if r["soft"] else ""
        print(f"{r['date'][:10]} | {r['title'][:64]:64} | {r['company'][:22]:22} | wl={r['wl'][:16]:16} | ratio={r['ratio']:.2f} | exp={r['exp']} | {'/'.join(r['cats'])[:26]:26} | {soft}")
    json.dump(final, open(f"{WORKDIR}/finn_finalists.json","w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
