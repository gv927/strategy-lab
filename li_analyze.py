import json, re

with open("/home/ubuntu/li_details.json") as f:
    jobs = json.load(f)

# language-related keywords (case-insensitive) to surface requirement lines
pat = re.compile(r"(norwegian|norsk|flytende|fluent|language|språk|engelsk|english|nationally|dansk|swedish|svensk)", re.I)

for j in jobs:
    lines = [l.strip() for l in re.split(r"[\n•\u2022]", j["desc"]) if l.strip()]
    hits = []
    for l in lines:
        if pat.search(l):
            hits.append(l[:400])
    print("=" * 100)
    print(f"{j['id']} | {j['title']} @ {j['company']} | {j['location']} | posted: {j['posted']}")
    print(f"LANG HITS ({len(hits)}):")
    for h in hits[:12]:
        print("   *", h)
    print("FIRST 500 CHARS:", j["desc"][:500].replace("\n", " | "))
