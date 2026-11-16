import json
final_ids = ["4474993966", "4478505398", "4464628956", "4478872124",
             "4474098218", "4482482039", "4481564952", "4470998122"]
cards = []
for f in ["/home/ubuntu/li_cards.json", "/home/ubuntu/li_cards2.json"]:
    with open(f) as fh:
        cards.extend(json.load(fh))
for j in cards:
    if j["id"] in final_ids:
        print(j["id"], "|", j["link"])
