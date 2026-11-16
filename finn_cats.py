#!/usr/bin/env python3
"""Explore finn job category/location URLs for a broader Oslo listing pool."""
import re, subprocess, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
def get(url):
    p = subprocess.run(["curl","-sL","--max-time","45","-w","\n__CODE__%{http_code}","-H",f"User-Agent: {UA}",url],capture_output=True,text=True).stdout
    code = p.rsplit("__CODE__",1)[-1] if "__CODE__" in p else "?"
    body = p.rsplit("__CODE__",1)[0]
    return code, body

urls = [
 "https://www.finn.no/job/oslo",
 "https://www.finn.no/job/category/finans",
 "https://www.finn.no/job/category/salgs",
 "https://www.finn.no/job/category/kundeservice",
 "https://www.finn.no/job/category/administrasjon",
 "https://www.finn.no/job/category/marketing",
 "https://www.finn.no/job/category/bank",
 "https://www.finn.no/job/category/okonomi",
]
for u in urls:
    code, body = get(u)
    ids = re.findall(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"', body)
    tm = re.search(r'class="sr-only">(\d+)\s*resultater', body)
    title = re.search(r"<title>(.*?)</title>", body, re.S)
    print(code, len(body), "cards=", len(ids), "results=", tm.group(1) if tm else "?", "|", u, "|", (title.group(1)[:70] if title else ""))
