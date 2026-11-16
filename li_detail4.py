import sys, json, time
sys.path.insert(0, "/home/ubuntu")
from li_detail import fetch, extract

ids = ["4482486652", "4479788248", "4471750620", "4476466493", "4455142299",
       "4481941539", "4358580068", "4335537543", "4481153383", "4468167228",
       "4479317444", "4480930986"]
out = []
for jid in ids:
    try:
        doc = fetch(jid)
        title, company, loc, desc, posted = extract(doc)
        out.append({"id": jid, "title": title, "company": company, "location": loc, "posted": posted, "desc": desc})
        print(f"{jid}: OK title={title!r} company={company!r} loc={loc!r} desc_len={len(desc)} posted={posted!r}")
    except Exception as e:
        print(f"{jid}: ERROR {e}")
    time.sleep(2.5)
with open("/home/ubuntu/li_details4.json", "w") as f:
    json.dump(out, f, indent=1)
print("saved", len(out))
