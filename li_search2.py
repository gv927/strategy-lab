import urllib.request, urllib.parse, re, html as htmlmod, json, time, sys

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch(kw, start=0):
    qs = urllib.parse.urlencode({"keywords": kw, "location": "Oslo, Norway", "start": start})
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?" + qs
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                time.sleep(8 + 6 * attempt)
                continue
            raise

def clean(s):
    return htmlmod.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s))).strip()

def parse(doc, kw):
    chunks = re.split(r'(?=<div class="base-card[^"]*"[^>]*data-entity-urn="urn:li:jobPosting:\d+"[^>]*>)', doc)
    out = []
    for blk in chunks[1:]:
        jid = re.search(r'data-entity-urn="urn:li:jobPosting:(\d+)"', blk)
        if not jid:
            continue
        jid = jid.group(1)
        t = re.search(r'<h3 class="base-search-card__title">(.*?)</h3>', blk, re.S)
        c = re.search(r'<h4 class="base-search-card__subtitle">(.*?)</h4>', blk, re.S)
        l = re.search(r'<span class="job-search-card__location">(.*?)</span>', blk, re.S)
        d = re.search(r'<time class="job-search-card__listdate[^"]*"[^>]*datetime="([^"]+)"(.*?)</time>', blk, re.S)
        href = re.search(r'href="(https://[a-z]+\.linkedin\.com/jobs/view/[^"?]+)', blk)
        title = clean(t.group(1)) if t else ""
        company = clean(c.group(1)) if c else ""
        if not company:
            slug = re.search(r'-at-([a-z0-9-]+)-' + jid, href.group(1)) if href else None
            if slug:
                company = slug.group(1).replace("-", " ").title()
        posted = d.group(1) if d else ""
        rel = clean(d.group(2)) if d else ""
        link = (href.group(1) if href else "https://no.linkedin.com/jobs/view/%s/" % jid)
        out.append({"id": jid, "title": title, "company": company,
                    "location": clean(l.group(1)) if l else "", "posted": posted,
                    "posted_rel": rel, "link": htmlmod.unescape(link), "kw": kw})
    return out

if __name__ == "__main__":
    searches = sys.argv[1:]
    seen, all_jobs = set(), []
    for kw in searches:
        try:
            doc = fetch(kw, 0)
            jobs = parse(doc, kw)
            print(f"[{kw}] {len(jobs)} cards")
            for j in jobs:
                key = j["id"]
                if key not in seen and j["title"]:
                    seen.add(key)
                    all_jobs.append(j)
        except Exception as e:
            print(f"[{kw}] ERROR: {e}")
        time.sleep(2.5)
    with open("/home/ubuntu/li_cards.json", "w") as f:
        json.dump(all_jobs, f, indent=1)
    print("TOTAL unique cards:", len(all_jobs))
    for j in all_jobs[:200]:
        print(f"{j['id']} | {j['posted']} ({j['posted_rel']}) | {j['title']} @ {j['company']} | {j['location']} | kw={j['kw']}")
