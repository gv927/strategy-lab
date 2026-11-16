import json

with open("/home/ubuntu/li_details.json") as f:
    jobs1 = {j["id"]: j for j in json.load(f)}

for jid in ["4481564952", "4482482039", "4464628956"]:
    j = jobs1[jid]
    print("=" * 90)
    print(f"FULL: {jid} | {j['title']} @ {j['company']} | {j['location']} | posted {j['posted']}")
    print(j["desc"])
