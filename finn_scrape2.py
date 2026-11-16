#!/usr/bin/env python3
"""Second scrape pass: more keywords + deeper pages. Merge with existing cards."""
import json, re, subprocess, sys, time, html, urllib.parse

WORKDIR = "/home/ubuntu/.hermes/cache/scratch"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

KEYWORDS2 = [
    "risk", "compliance", "treasury", "wealth", "loan", "insurance", "broker",
    "investment", "payments", "onboarding", "business developer", "digital marketer",
    "marketing manager", "content manager", "social media", "growth", "business analyst",
    "operations", "office manager", "executive assistant", "customer success",
    "inside sales", "sales development", "lead generation", "CRM", "KYC",
    "risiko", "etterlevelse", "marked", "vekst", "kontorleder", "markedssjef",
    "salgsdirektør", "kundeservice", "kundemegling", "kundeseier", "rådgiver",
    "økonomiansvarlig", "finans", "bank", "økonomi", "salg", "administrasjon",
    "reklame", "markedsføring", "digital markedsføring", "kontorassistent",
    "servicemedarbeider", "kundemedarbeider", "rådgiver bank", "kunderådgiver",
    "compliance officer", "risk analyst", "aml analyst", "financial controller",
    "accountant", "credit analyst", "procurement", "business intelligence",
    "product marketing", "brand manager", "campaign manager", "web analyst",
]

def fetch(url):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "45", "-H", f"User-Agent: {UA}",
                            "-H", "Accept-Language: en-US,en;q=0.9,nb;q=0.8", url],
                           capture_output=True, text=True, timeout=60)
        return r.stdout
    except Exception:
        return ""

def strip_tags(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", s, flags=re.I)
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    lines = [WS_RE.sub(" ", l).strip() for l in s.split("\n")]
    return "\n".join(l for l in lines if l)

def parse_cards(page):
    out = []
    for m in re.finditer(r'<article[^>]*class="[^"]*job-card-article[^"]*"[^>]*id="(\d+)"(.*?)</article>', page, re.S):
        aid, blob = m.group(1), m.group(2)
        tm = re.search(r'<a[^>]*class="[^"]*job-card-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blob, re.S)
        if not tm:
            continue
        title = WS_RE.sub(" ", strip_tags(tm.group(2))).strip()
        cm = re.search(r"<strong[^>]*>(.*?)</strong>", blob, re.S)
        comp = WS_RE.sub(" ", strip_tags(cm.group(1))).strip() if cm else ""
        lm = re.search(r'class="[^"]*truncate[^"]*"[^>]*>(.*?)</span>', blob, re.S)
        loc = WS_RE.sub(" ", strip_tags(lm.group(1))).strip() if lm else ""
        dm = re.search(r'dateTime="([^"]+)"', blob)
        out.append({"id": aid, "title": title, "company": comp, "location": loc,
                    "date": dm.group(1) if dm else "", "url": f"https://www.finn.no/job/ad/{aid}"})
    return out

def main():
    cards = {c["id"]: c for c in json.load(open(f"{WORKDIR}/finn_cards.json"))}
    before = len(cards)
    for kw in KEYWORDS2:
        for page in (1, 2, 3):
            url = f"https://www.finn.no/job/search?q={urllib.parse.quote(kw)}" + (f"&page={page}" if page > 1 else "")
            got = parse_cards(fetch(url))
            print(f"kw={kw} p={page} n={len(got)}", file=sys.stderr)
            for c in got:
                c["keyword"] = kw
                if c["id"] not in cards:
                    cards[c["id"]] = c
            time.sleep(0.35)
    json.dump(list(cards.values()), open(f"{WORKDIR}/finn_cards.json", "w"), ensure_ascii=False, indent=1)
    print(f"before={before} after={len(cards)}")

if __name__ == "__main__":
    main()
