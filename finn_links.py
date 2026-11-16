#!/usr/bin/env python3
import re, subprocess
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}","https://www.finn.no/job/search?q=bank"],capture_output=True,text=True).stdout
links = sorted(set(re.findall(r'href="(/job/[^"#?]+)"', p)))
for l in links[:120]:
    print(l)
print("---- count", len(links))
