#!/usr/bin/env python3
"""Final verification of chosen shortlist: language gate + liveness + requirement text."""
import json, re, sys, subprocess, importlib.util
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
spec = importlib.util.spec_from_file_location("l3", "/home/ubuntu/finn_lang3.py")
l3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

CHOICE = [
 "479887944","479315446","479298541","479296699","479165637","479606136","479780044",
 "479681235","479094841","478557358","478722802","478571145","479289509","479661118",
 "478233639","479100039","476769155","478864351","479898028","478762579","479353094",
 "479911811","479851225","479680710","477953539","478149003","479149003",
]

def fetch(url):
    try:
        r = subprocess.run(["curl","-sL","--max-time","40","-H",f"User-Agent: {UA}",
                            "-H","Accept-Language: en-US,en;q=0.9,nb;q=0.8",url],
                           capture_output=True,text=True,timeout=55)
        return r.stdout
    except Exception:
        return ""

def req_bullets(body):
    lines = body.split("\n")
    try:
        i = lines.index("Kvalifikasjoner")
    except ValueError:
        return []
    out = []
    for l in lines[i+1:i+14]:
        if l.strip() in ("Hva vi tilbyr","Er du en god match for denne stillingen?","Vis mindre"):
            break
        if l.strip(): out.append(l.strip())
    return out

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    for i in CHOICE:
        d = det.get(i)
        if not d:
            print("MISSING", i); continue
        body = d.get("body","")
        hard, soft = l3.evaluate(body)
        page = fetch(d["url"])
        live = bool(re.search(r"job/ad/\d+", page)) and len(page) > 30000
        title_html = re.search(r"<title>(.*?)</title>", page, re.S)
        print("="*108)
        print(f"[{'LIVE' if live else 'CHECK'}] {d['title']}")
        print(f"  company: {d.get('company','')} | location: {d.get('location','')} | posted: {d.get('date','')[:10]} | info: {d.get('info',{})}")
        print(f"  url: {d['url']}  | html_title: {(title_html.group(1)[:70] if title_html else 'n/a')}")
        print(f"  LANGUAGE-REQ hits: hard={len(hard)} soft={len(soft)}")
        for h in hard[:3]: print(f"     HARD> {h[:190]}")
        for s in soft[:2]: print(f"     soft> {s[:190]}")
        print(f"  REQS: {' | '.join(req_bullets(body)[:9])}")

if __name__ == "__main__":
    main()
