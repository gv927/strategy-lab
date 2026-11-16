#!/usr/bin/env python3
"""Fetch a single NAV ad page and extract readable text to find the ad URL format and content."""
import re, html, urllib.request, sys

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")

uuid = sys.argv[1] if len(sys.argv) > 1 else "1ebff0d5-ec1f-4464-b15e-3108c559e04e"
for path in [f"https://arbeidsplassen.nav.no/stilling/{uuid}", f"https://arbeidsplassen.nav.no/stillinger/stilling/{uuid}"]:
    try:
        raw = fetch(path)
        print("URL OK:", path, "len:", len(raw))
        # strip scripts/styles/tags
        raw2 = re.sub(r"<script[\s\S]*?</script>", " ", raw)
        raw2 = re.sub(r"<style[\s\S]*?</style>", " ", raw2)
        text = re.sub(r"<[^>]+>", " ", raw2)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text)
        print(text[:3000])
        break
    except Exception as e:
        print("URL FAIL:", path, e)
