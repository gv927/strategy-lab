#!/usr/bin/env python3
import re, subprocess
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
p = subprocess.run(["curl","-sL","--max-time","45","-H",f"User-Agent: {UA}","https://www.finn.no/job/search?q=bank"],capture_output=True,text=True).stdout
i = p.find("Oslo<!-- --> <span")
print(p[max(0,i-6000):i+3000])
