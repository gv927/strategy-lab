import urllib.request, urllib.parse, re
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
qs = urllib.parse.urlencode({"keywords": "customer service", "location": "Oslo, Norway", "start": 0})
url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?" + qs
req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
with urllib.request.urlopen(req, timeout=30) as r:
    doc = r.read().decode("utf-8", "replace")
# print first card block fully
m = re.search(r'<li[^>]*>(.*?)</li>', doc, re.S)
if m:
    print(m.group(1)[:3500])
