import json
with open("/home/ubuntu/li_details4.json") as f:
    jobs = {j["id"]: j for j in json.load(f)}
for jid in ["4471750620", "4476466493", "4455142299", "4480930986"]:
    j = jobs[jid]
    print("=" * 90)
    print(f"FULL: {jid} | {j['title']} @ {j['company']} | {j['location']} | posted {j['posted']}")
    print(j["desc"][:5500])
