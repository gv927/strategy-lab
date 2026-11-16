import sys, json, time
sys.path.insert(0, "/home/ubuntu")
from li_search2 import fetch, parse

searches = ["fintech", "compliance", "AML", "customer relationship", "digital marketing", "business development", "administration"]
seen, all_jobs = set(), []
for kw in searches:
    try:
        doc = fetch(kw, 0)
        jobs = parse(doc, kw)
        print(f"[{kw}] {len(jobs)} cards")
        for j in jobs:
            if j["id"] not in seen and j["title"]:
                seen.add(j["id"])
                all_jobs.append(j)
    except Exception as e:
        print(f"[{kw}] ERROR: {e}")
    time.sleep(2.5)
with open("/home/ubuntu/li_cards2.json", "w") as f:
    json.dump(all_jobs, f, indent=1)
print("TOTAL unique new cards:", len(all_jobs))
for j in all_jobs:
    print(f"{j['id']} | {j['posted']} ({j['posted_rel']}) | {j['title']} @ {j['company']} | {j['location']} | kw={j['kw']}")
