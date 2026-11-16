#!/usr/bin/env python3
"""Print language context windows for shortlisted candidates for manual verification."""
import json, re, sys, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("fl", "/home/ubuntu/finn_lang.py")
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)

def show(r, detail=900):
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    d = det[r["id"]]
    body = d["body"]
    print("="*110)
    print(f"{r['title']}\n{r['company']} | {r['location']} | {r['date'][:10]} | wl={r['wl']} | {r['url']}")
    print(f"cats={r['cats']} exp={r['exp']}")
    # language-related windows
    pat = r"(norsk|norwegian|english|engelsk|språk|language|fluen\w*|proficien\w*|behersk\w*|scandinav\w*|nordisk)"
    seen = []
    for m in re.finditer(pat, body, re.I):
        a = max(0, m.start()-130); b = min(len(body), m.end()+130)
        w = fl.WS_RE.sub(" ", body[a:b].replace("\n"," "))
        if w not in seen:
            seen.append(w)
    for w in seen[:14]:
        print("  ...", w)
    print("--- body head ---")
    print(body[:detail])

if __name__ == "__main__":
    ok = json.load(open(f"{WORKDIR}/finn_lang_ok.json"))
    ids = sys.argv[1:] if len(sys.argv) > 1 else None
    for r in ok:
        if ids and r["id"] not in ids: continue
        show(r)
