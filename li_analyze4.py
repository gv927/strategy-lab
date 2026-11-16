import json, re

with open("/home/ubuntu/li_details2.json") as f:
    jobs2 = {j["id"]: j for j in json.load(f)}

# 1) language check for KLP + Kinly
for jid in ["4478993949", "4480361850"]:
    j = jobs2[jid]
    d = j["desc"]
    nor_words = len(re.findall(r"\b(og|for|med|som|til|ved|av|på|fra|du|vi|vår|har|skal|kan|vil|eller|inneholder|ansvar|kundeservice|erfaring|utdannelse|søknad)\b", d, re.I))
    print("=" * 90)
    print(f"{jid} | {j['title']} @ {j['company']}")
    print("FIRST 400:", d[:400].replace("\n", " "))
    print(f"Norwegian-word density: {nor_words}")
    # any sentence about application/requirements
    for m in re.finditer(r"(kvalifis|erfaring|språk|language|engelsk|norsk)[^.]{0,300}", d, re.I):
        print("  >", m.group(0)[:350].replace("\n", " "))

with open("/home/ubuntu/li_details.json") as f:
    jobs1 = {j["id"]: j for j in json.load(f)}

# 2) full text of survivor candidates
for jid in ["4474993966", "4474098218", "4478505398", "4478872124"]:
    src = jobs2 if jid in jobs2 else jobs1
    j = src[jid]
    print("=" * 90)
    print(f"FULL: {jid} | {j['title']} @ {j['company']} | {j['location']} | posted {j['posted']}")
    print(j["desc"])
