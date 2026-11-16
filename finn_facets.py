#!/usr/bin/env python3
import re, subprocess
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}","https://www.finn.no/job/search?q=bank"],capture_output=True,text=True).stdout
print("len", len(p))
for pat in ["category", "geoId", "county", "Oslo", "fylke", "arbeidssprak", "language"]:
    idxs = [m.start() for m in re.finditer(pat, p, re.I)][:3]
    print(f"--- {pat}: {len(re.findall(pat,p,re.I))} hits")
    for i in idxs:
        print("   ", p[max(0,i-120):i+160].replace("\n"," ")[:300])
# any href patterns at all
hrefs = sorted(set(re.findall(r'href="([^"]{3,80})"', p)))
print("sample hrefs:", hrefs[:40])
