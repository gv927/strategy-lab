#!/usr/bin/env python3
"""Fetch finn ad detail pages for Oslo candidate listings, extract text + language info."""
import json, re, subprocess, sys, time, html, os

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

def fetch(url):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "40", "-H", f"User-Agent: {UA}",
                            "-H", "Accept-Language: en-US,en;q=0.9,nb;q=0.8", url],
                           capture_output=True, text=True, timeout=55)
        return r.stdout
    except Exception:
        return ""

def strip_tags(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>", "\n", s, flags=re.I)
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    lines = [WS_RE.sub(" ", l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def extract_body(page):
    """Get main ad body text."""
    m = re.search(r'<div[^>]*id="[^"]*ad-body[^"]*"[^>]*>(.*?)</div>\s*</div>', page, re.S)
    blob = m.group(1) if m else page
    # remove similar-ads section
    blob = re.split(r"Lignende annonser|Andre jobber", blob)[0]
    return strip_tags(blob)

def key_info(page):
    info = {}
    for m in re.finditer(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', page, re.S):
        k = WS_RE.sub(" ", strip_tags(m.group(1))).strip()
        v = WS_RE.sub(" ", strip_tags(m.group(2))).strip()
        if k:
            info[k] = v
    # finn style: <span class="key-info-label">..</span> ... <strong class="key-info-text">..
    for m in re.finditer(r'key-info-label[^>]*>(.*?)</span>.*?key-info-text[^>]*>(.*?)</strong>', page, re.S):
        k = WS_RE.sub(" ", strip_tags(m.group(1))).strip()
        v = WS_RE.sub(" ", strip_tags(m.group(2))).strip()
        if k:
            info.setdefault(k, v)
    return info

def main():
    rel = json.load(open(f"{WORKDIR}/finn_oslo_rel.json"))
    out_path = f"{WORKDIR}/finn_details.json"
    existing = {}
    if os.path.exists(out_path):
        existing = {d["id"]: d for d in json.load(open(out_path))}
    print(f"candidates={len(rel)} existing={len(existing)}")
    for i, c in enumerate(rel):
        aid = c["id"]
        if aid in existing and existing[aid].get("body_len", 0) > 200:
            continue
        page = fetch(c["url"])
        body = extract_body(page)
        info = key_info(page)
        existing[aid] = {**c, "body": body, "info": info, "body_len": len(body)}
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(rel)}", file=sys.stderr)
            json.dump(list(existing.values()), open(out_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(0.4)
    json.dump(list(existing.values()), open(out_path, "w"), ensure_ascii=False, indent=1)
    print("saved", len(existing))

if __name__ == "__main__":
    main()
