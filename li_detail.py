import urllib.request, re, html as htmlmod, json, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE = "https://no.linkedin.com/jobs/view/%s"

def fetch(jid):
    for attempt in range(4):
        try:
            req = urllib.request.Request(BASE % jid, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                time.sleep(10 + 8 * attempt)
                continue
            raise

def clean(s):
    return htmlmod.unescape(re.sub(r"\n{2,}", "\n", re.sub(r"<[^>]+>", " ", s))).strip()

def extract(doc):
    t = re.search(r'<h1[^>]*class="[^"]*top-card-layout__title[^"]*"[^>]*>(.*?)</h1>', doc, re.S) \
        or re.search(r'<h2[^>]*class="[^"]*top-card-layout__title[^"]*"[^>]*>(.*?)</h2>', doc, re.S)
    c = re.search(r'<span[^>]*class="[^"]*topcard__flavor[^"]*"[^>]*>\s*<a[^>]*>(.*?)</a>', doc, re.S) \
        or re.search(r'<a[^>]*class="[^"]*topcard__org-name-link[^"]*"[^>]*>(.*?)</a>', doc, re.S) \
        or re.search(r'<span[^>]*class="[^"]*topcard__flavor[^"]*"[^>]*>(.*?)</span>', doc, re.S)
    l = re.search(r'<span[^>]*class="[^"]*topcard__flavor--bullet[^"]*"[^>]*>(.*?)</span>', doc, re.S)
    d = re.search(r'<div[^>]*class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', doc, re.S)
    pd = re.search(r'<span[^>]*class="[^"]*posted-time[^"]*"[^>]*>(.*?)</span>', doc, re.S) \
         or re.search(r'"datePosted"\s*:\s*"([^"]+)"', doc)
    title = clean(t.group(1)) if t else ""
    company = clean(c.group(1)) if c else ""
    loc = clean(l.group(1)) if l else ""
    desc = clean(d.group(1)) if d else ""
    posted = clean(pd.group(1)) if pd else ""
    return title, company, loc, desc, posted

if __name__ == "__main__":
    import sys
    out = []
    for jid in sys.argv[1:]:
        try:
            doc = fetch(jid)
            title, company, loc, desc, posted = extract(doc)
            out.append({"id": jid, "title": title, "company": company, "location": loc, "posted": posted, "desc_len": len(desc), "desc": desc})
            print(f"{jid}: OK  len={len(doc)}  title={title!r} company={company!r} loc={loc!r} desc_len={len(desc)} posted={posted!r}")
        except Exception as e:
            print(f"{jid}: ERROR {e}")
        time.sleep(2.5)
    with open("/home/ubuntu/li_details.json", "w") as f:
        json.dump(out, f, indent=1)
    print("saved", len(out), "details")
