#!/usr/bin/env python3
"""Show raw HTML around first ad link to design card parser."""
import re, sys, urllib.request

UA = {'User-Agent': 'Mozilla/5.0'}
url = sys.argv[1]
req = urllib.request.Request(url, headers=UA)
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read().decode("utf-8", "replace")
i = raw.find('href="/stillinger/stilling/')
print(repr(raw[i-200:i+3500]))
