#!/usr/bin/env python3
"""Final hard-cue language gate + liveness check on the candidate set."""
import json, re, subprocess, sys, html
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# explicit "must be able to do X in Norwegian" cues -> always a hard requirement
HARD_CUE = [
    r"fluen\w*\s+(?:i\s+)?norsk", r"fluen\w*\s+(?:i\s+)?norwegian", r"norsk\w*\s+og\s+engelsk",
    r"norsk\w*\s+eller\s+engelsk", r"norsk\w*\s+som\s+arbeidsspråk", r"norsk\s+er\s+arbeidsspråk",
    r"norsk[^.]{0,45}(?:språk|beherskes|må\s+kunne|må\s+beherske|er\s+et\s+krav|er\s+krav|påkrevd|"
    r"krav|grunnleggende\s+norsk)", r"norsk[^.]{0,30}(?:proficien\w*|språkkunnskap|ferdighet\w*)",
    r"(?:good|strong|excellent|solid)\s+(?:command|knowledge|proficiency|skills)[^.]{0,35}norsk",
    r"norsk[^.]{0,35}(?:språklig|grammatikk|forstår\w*)",
    r"norwegian\s+language\s+skills", r"norwegian\s+on\s+a\s+fluent", r"norwegian\s+fluen\w*",
    r"norwegian\s+proficien\w*", r"working\s+language\s+will\s+be\s+norwegian",
    r"everyday\s+working\s+language", r"ditt\s+arbeidsspråk[^.]{0,30}norsk",
    r"arbeidsspråk[^.]{0,30}norsk", r"norsk[^.]{0,30}arbeidsspråk",
    r"behersk\w*[^.]{0,30}norsk", r"snakker[^.]{0,25}norsk", r"skriver[^.]{0,25}norsk",
    r"skandinavis\w*\s+(?:språk|language)", r"ett\s+skandinavisk", r"et\s+skandinavisk",
    r"nordisk\s+språk", r"(?:a\s+)?scandinavian\s+language", r"norsk[^.]{0,25}\band\s+english",
    r"english\s+and\s+norsk", r"norsk[^.]{0,40}\bog\s+engelsk", r"norsk[^.]{0,25}(?:og|and)\s+engelsk",
    r"god\s+norsk", r"gode\s+norsk", r"norsk\w*\s+nivå\s*[ab]\d", r"b2\s+norsk",
    r"norsk[^.]{0,30}nivå", r"norsk[^.]{0,30}må\s+beherskes", r"norsk[^.]{0,20}\bis\s+(?:et\s+)?krav",
]
# explicit soft cues (requirement waived)
SOFT_CUE = [
    r"norsk[^.]{0,40}(?:er\s+en\s+fordel|er\s+et\s+pluss|pluss\s+til|fordel|an\s+advantage|"
    r"is\s+an?\s+advantage|is\s+a\s+plus|nice\s+to\s+have|optional|preferred|er\s+ønskelig)",
    r"proficien\w*\s+in\s+norwegian[^.]{0,30}(?:an\s+advantage|is\s+an?\s+advantage|is\s+a\s+plus|"
    r"nice\s+to\s+have)", r"norwegian[^.]{0,30}(?:language\s+skills|skills)[^.]{0,30}(?:an\s+advantage|"
    r"is\s+a\s+plus|nice\s+to\s+have|will\s+be\s+considered\s+an\s+advantage)",
    r"(?:a\s+)?scandinavian\s+language[^.]{0,40}(?:an\s+advantage|is\s+a\s+plus|nice\s+to\s+have|"
    r"considered\s+an\s+advantage)", r"norwegian\s+is\s+an\s+advantage",
    r"knowledge\s+of\s+norwegian[^.]{0,60}(?:advantage|but\s+not\s+a\s+requirement)",
    r"knowledge\s+of\s+the\s+norwegian[^.]{0,60}(?:advantage|but\s+not\s+a\s+requirement)",
]

def windows(text, pat, w=170):
    out = []
    rx = pat if hasattr(pat, "finditer") else re.compile(pat, re.I)
    for m in rx.finditer(text):
        a = max(0, m.start()-w); b = min(len(text), m.end()+w)
        out.append(" ".join(text[a:b].replace("\n", " ").split()))
    return out

def hard_hits(body):
    hits = []
    for p in HARD_CUE:
        for w in windows(body, p):
            # soft marker inside the same clause cancels it (only if it directly qualifies)
            clause = w
            if re.search(r"(advantage|pluss|fordel|nice to have|optional|preferred|but not a requirement|"
                         r"will be considered)", clause, re.I) and not re.search(
                         r"(fluen\w*\s+(?:i\s+)?norsk|fluen\w*\s+(?:i\s+)?norwegian|"
                         r"norsk\w*\s+og\s+engelsk|working language will be norwegian)", clause, re.I):
                continue
            hits.append((p, w))
    return hits

def alive(url):
    try:
        r = subprocess.run(["curl","-sL","--max-time","35","-H",f"User-Agent: {UA}",url],
                           capture_output=True, text=True, timeout=50)
        page = r.stdout
    except Exception:
        return None, ""
    if "annonsen kan være utløpt" in page.lower() or "utløpt" in page.lower() and "job/ad" not in page.lower():
        pass
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    t = (title.group(1) if title else "")[:120]
    ok = bool(re.search(r"job/ad/\d+", page)) and len(page) > 30000
    return ok, t

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    cands = json.load(open(f"{WORKDIR}/finn_no_no_req.json"))
    rows = []
    for r in cands:
        body = det[r["id"]].get("body", "")
        h = hard_hits(body)
        alive_flag, t = alive(r["url"]) if "--live" in sys.argv else (None, "")
        rows.append({**r, "hard_hits": h, "alive": alive_flag, "page_title": t})
    json.dump(rows, open(f"{WORKDIR}/finn_gate.json","w"), ensure_ascii=False, indent=1)
    keep = [r for r in rows if not r["hard_hits"]]
    print("after hard-cue gate:", len(keep), "of", len(rows))
    for r in sorted(keep, key=lambda x: x["date"], reverse=True):
        print(f"{r['date']} | {r['title'][:62]:62} | {r['company'][:22]:22} | wl={r['wl'][:16]:16} | {r['id']}")
    json.dump(keep, open(f"{WORKDIR}/finn_gate_pass.json","w"), ensure_ascii=False, indent=1)
    print()
    print("=== blocked (hard Norwegian cues) ===")
    for r in rows:
        if r["hard_hits"]:
            print(f"{r['title'][:70]} | {r['company'][:24]} | {r['id']}")
            for p, w in r["hard_hits"][:2]:
                print(f"    -> {w[:200]}")

if __name__ == "__main__":
    main()
