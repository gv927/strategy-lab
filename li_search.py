import urllib.request, urllib.parse, re, html as htmlmod, json, time, sys

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch(kw, start=0):
    qs = urllib.parse.urlencode({"keywords": kw, "location": "Oslo, Norway", "start": start})
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?" + qs
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def parse(html_doc):
    cards = re.findall(r'<li[^>]*data-entity-urn="urn:li:jobPosting:(\d+)"[^>]*>(.*?)</li>', html_doc, re.S)
    out = []
    for jid, blk in cards:
        t = re.search(r'<h3[^>]*>\s*<span[^>]*>(.*?)</span>', blk) or re.search(r'<h3[^>]*>(.*?)</h3>', blk, re.S)
        title = htmlmod.unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip() if t else ""
        c = re.search(r'<h4[^>]*>\s*<a[^>]*>(.*?)</a>', blk, re.S) or re.search(r'<h4[^>]*>(.*?)</h4>', blk, re.S)
        company = htmlmod.unescape(re.sub(r'<[^>]+>', '', c.group(1))).strip() if c else ""
        l = re.search(r'job-search-card__location[^"]*"[^>]*>\s*(.*?)\s*</span>', blk, re.S)
        loc = htmlmod.unescape(re.sub(r'<[^>]+>', '', l.group(1))).strip() if l else ""
        link = "https://no.linkedin.com/jobs/view/%s/" % jid
        # company fallback from URL slug
        if not company:
            slug = re.search(r'jobs/view/\d+-[^/]*?-at-([a-z0-9-]+)', blk)
            if slug:
                company = slug.group(1).replace('-', ' ').title()
        out.append({"id": jid, "title": title, "company": company, "location": loc, "link": link})
    return out

searches = sys.argv[1:]
seen, all_jobs = set(), []
for kw in searches:
    for pg in (0, 10):
        try:
            doc = fetch(kw, pg)
            jobs = parse(doc)
            print(f"[{kw} start={pg}] {len(jobs)} cards")
            for j in jobs:
                key = (j["title"].lower(), j["company"].lower(), j["id"])
                if key not in seen and j["title"]:
                    seen.add(key)
                    all_jobs.append({**j, "kw": kw})
        except Exception as e:
            print(f"[{kw} start={pg}] ERROR: {e}")
        time.sleep(1.5)

with open("/home/ubuntu/li_cards.json", "w") as f:
    json.dump(all_jobs, f, indent=1)
print(f"TOTAL unique cards: {len(all_jobs)}")
