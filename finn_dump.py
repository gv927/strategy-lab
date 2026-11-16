#!/usr/bin/env python3
"""Dump full language-context windows for manual verification of shortlisted ads."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
WS_RE = re.compile(r"\s+")

def main():
    review = json.load(open(f"{WORKDIR}/finn_review.json"))
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    only_clean = "--clean" in sys.argv
    ids = [a for a in sys.argv[1:] if not a.startswith("--")]
    pat = r"(norsk|norwegian|english|engelsk|språk|language|fluen\w*|proficien\w*|behersk\w*|scandinav\w*|nordisk|native)"
    for r in review:
        if only_clean and r["hard"]:
            continue
        if ids and r["id"] not in ids:
            continue
        body = det[r["id"]]["body"]
        print("="*115)
        print(f"{r['title']}\n{r['company']} | {r['location']} | {r['date'][:10]} | wl={r['wl']} | exp={r['exp']}\n{r['url']}")
        seen = []
        for m in re.finditer(pat, body, re.I):
            a = max(0, m.start()-135); b = min(len(body), m.end()+135)
            w = WS_RE.sub(" ", body[a:b].replace("\n", " "))
            if w not in seen:
                seen.append(w)
        for w in seen[:12]:
            print("   ...", w)
        print("  --BODY HEAD--")
        print("   " + body[:700].replace("\n", "\n   "))

if __name__ == "__main__":
    main()
