import json

final_ids = ["4471750620", "4479788248", "4455142299", "4480930986", "4474993966",
             "4478505398", "4464628956", "4478872124", "4482482039", "4474098218"]
cards = []
for f in ["/home/ubuntu/li_cards.json", "/home/ubuntu/li_cards2.json", "/home/ubuntu/li_cards3.json"]:
    with open(f) as fh:
        cards.extend(json.load(fh))
uniq = {}
for c in cards:
    uniq.setdefault(c["id"], c)
print("unique cards across all searches:", len(uniq))
for fid in final_ids:
    c = uniq.get(fid)
    print(fid, "->", c["link"] if c else "MISSING")

# details verified count
for f in ["li_details.json", "li_details2.json", "li_details3.json", "li_details4.json"]:
    with open("/home/ubuntu/" + f) as fh:
        d = json.load(fh)
    print(f, len(d), "detail pages,", sum(1 for x in d if x["desc"]), "with descriptions")
