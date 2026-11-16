#!/usr/bin/env python3
"""Definitive language-requirement scan over candidate ads; prints every relevant line."""
import json, re, sys
WORKDIR = "/home/ubuntu/.hermes/cache/scratch"

# Any line (bullet/sentence) that mentions a Norwegian/Scandinavian/Nordic language ability
PAT = re.compile(r"[^\n]{0,200}(norsk|norwegian|scandinav\w*|nordic|nordisk|skandinav\w*)[^\n]{0,200}", re.I)
# markers that turn a mention into a hard requirement
HARD = re.compile(r"(fluen\w*|proficien\w*|behersk\w*|strong\s+(?:written\s+and\s+)?spoken|"
                   r"excellent\s+(?:written\s+and\s+)?spoken|good\s+(?:command|proficiency)|"
                   r"krav|påkrevd|required|must\s+have|must\s+speak|daily\s+working\s+language|"
                   r"working\s+language\s+will\s+be|er\s+et\s+krav|må\s+(?:kunne|beherske|snakke)|"
                   r"solid\s+knowledge|knowledge\s+of|proficiency\s+in|level\s+b2|b2\b|"
                   r"norsk\w*\s+som\s+arbeidsspråk|arbeidsspråk)", re.I)
SOFT = re.compile(r"(is\s+an\s+advantage|an\s+advantage|is\s+a\s+(?:plus|bonus)|nice\s+to\s+have|"
                   r"preferred|desirable|optional|but\s+not\s+a\s+requirement|er\s+et\s+pluss|"
                   r"pluss\s+til|er\s+en\s+fordel|consider(ed)?\s+an?\s+advantage|"
                   r"see\s+as\s+a\s+(?:bonus|plus)|nice\s+to\s+have|bonus)", re.I)

def main():
    det = {d["id"]: d for d in json.load(open(f"{WORKDIR}/finn_details_all.json"))}
    ids = sys.argv[1:]
    for i in ids:
        d = det.get(i)
        if not d:
            print("MISSING", i); continue
        body = d.get("body", "")
        print("="*110)
        print(f"{d['title']} | {d.get('company','')} | {d.get('location','')} | {d.get('date','')[:10]} | {d['url']}")
        print(f"   info: {d.get('info',{})}")
        seen = set()
        for m in PAT.finditer(body):
            line = " ".join(m.group(0).split())
            if line in seen:
                continue
            seen.add(line)
            if not re.search(r"(språk|language|fluen\w*|proficien\w*|behersk\w*|snakker|skriver|forstår\w*|"
                             r"ferdighet\w*|arbeidsspråk|og\s+engelsk|and\s+english|scandinav|nordic|"
                             r"nordisk|krav|påkrevd)", line, re.I):
                continue
            tag = "HARD" if HARD.search(line) else ("soft" if SOFT.search(line) else "ment")
            print(f"   [{tag}] {line[:300]}")

if __name__ == "__main__":
    main()
