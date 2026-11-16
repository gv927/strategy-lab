import json
with open("/home/ubuntu/li_details3.json") as f:
    jobs = {j["id"]: j for j in json.load(f)}
for jid in ["4470521160", "4470998122"]:
    j = jobs[jid]
    print("=" * 90)
    print(f"FULL: {jid} | {j['title']} @ {j['company']} | {j['location']} | posted {j['posted']}")
    print(j["desc"])
