#!/usr/bin/env python3
import re, subprocess, urllib.parse, html
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
def cards(url):
    p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}",url],capture_output=True,text=True).stdout
    ids = re.findall(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"', p)
    tm = re.search(r'class="sr-only">(\d+)\s*resultater', p)
    return len(ids), (tm.group(1) if tm else "?"), p
for kw in ["English","engelsk","English speaking","snakker engelsk","sales Oslo","bank Oslo","financial services Oslo"]:
    n, tot, _ = cards(f"https://www.finn.no/job/search?q={urllib.parse.quote(kw)}")
    print(f"{kw!r}: cards={n} total={tot}")
