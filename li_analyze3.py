import json, re

with open("/home/ubuntu/li_details2.json") as f:
    jobs = json.load(f)

lang_pat = re.compile(r"(norwegian|norsk|flytende|fluent|language|språk|engelsk|english|dansk|danish|swedish|svensk|scandinav)", re.I)

for j in jobs:
    d = j["desc"]
    print("=" * 100)
    print(f"{j['id']} | {j['title']} @ {j['company']} | {j['location']}")
    shown = []
    for m in lang_pat.finditer(d):
        s, e = max(0, m.start() - 250), min(len(d), m.end() + 250)
        if shown and s < shown[-1][1]:
            shown[-1] = (shown[-1][0], e)
        else:
            shown.append((s, e))
    if shown:
        for s, e in shown:
            print(f"  [LANG] ...{d[s:e]}...".replace("\n", " "))
    else:
        print("  [LANG] no language mentions at all")
