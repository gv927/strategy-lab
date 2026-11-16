#!/usr/bin/env python3
import re, subprocess
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}","https://www.finn.no/job/search?q=bank"],capture_output=True,text=True).stdout
start = p.find('id="filter-list"')
end = p.find('id="search-results"')
seg = p[start:end] if start>0 and end>start else p
# split sections by accordion buttons
parts = re.split(r'(<h3 class="t4 m-0">[^<]+</h3>)', seg)
cur = None
for part in parts:
    m = re.match(r'<h3 class="t4 m-0">([^<]+)</h3>', part)
    if m:
        cur = m.group(1); continue
    if cur is None: continue
    opts = re.findall(r'<w-checkbox><span class="[^"]*">([^<]+?)(?:<!-- --> <span class="text-s s-text-subtle">\(<!-- -->(\d+)<!-- -->\))?</span>', part)
    if opts:
        print(f"[{cur}]")
        for name, cnt in opts:
            print(f"   - {name} ({cnt})")
