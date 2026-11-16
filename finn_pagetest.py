#!/usr/bin/env python3
import json, re, subprocess, html, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>"); WS_RE = re.compile(r"\s+")
def strip_tags(s):
    s = re.sub(r"<script.*?</script>"," ",s,flags=re.S|re.I); s = re.sub(r"<style.*?</style>"," ",s,flags=re.S|re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>","\n",s,flags=re.I); s = TAG_RE.sub(" ",s); s = html.unescape(s)
    return "\n".join(WS_RE.sub(" ",l).strip() for l in s.split("\n") if WS_RE.sub(" ",l).strip())
def cards(url):
    p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}",url],capture_output=True,text=True).stdout
    ids = re.findall(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"', p)
    return ids, len(p)
for kw in ["bank","sales","kundeservice"]:
    for pg in (1,2,3):
        ids, n = cards(f"https://www.finn.no/job/search?q={urllib.parse.quote(kw)}" + (f"&page={pg}" if pg>1 else ""))
        print(kw, pg, "cards:", len(ids), "bytes:", n, "first:", ids[:3])
