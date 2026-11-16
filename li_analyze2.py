import json, re

with open("/home/ubuntu/li_details.json") as f:
    jobs = json.load(f)

ids = ["4476948945", "4482856677", "4472042272", "4477895042", "4477422143",
       "4475993684", "4480997140", "4482142928", "4432370536", "4478872124",
       "4464628956", "4478763834", "4482482039", "4478423396", "4473731940", "4481564952"]

lang_pat = re.compile(r"(norwegian|norsk|flytende|fluent|language|språk|engelsk|english|dansk|swedish|svensk|kommunikasjons)", re.I)
req_pat = re.compile(r"(qualification|requirement|what you bring|what we look for|who you are|about you|your profile|competence|erfaring|skills|kandidat|what you bring)", re.I)

for j in jobs:
    if j["id"] not in ids:
        continue
    d = j["desc"]
    print("=" * 100)
    print(f"{j['id']} | {j['title']} @ {j['company']}")
    # print windows around every language mention (250 chars context each side)
    shown = []
    for m in lang_pat.finditer(d):
        s, e = max(0, m.start() - 250), min(len(d), m.end() + 250)
        if shown and s < shown[-1][1]:
            shown[-1] = (shown[-1][0], e)
        else:
            shown.append((s, e))
    if shown:
        for s, e in shown:
            print(f"  [LANG {s}:{e}] ...{d[s:e]}...".replace("\n", " "))
    else:
        print("  [LANG] no language mentions at all")
