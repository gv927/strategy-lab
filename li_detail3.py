import sys, json, time
sys.path.insert(0, "/home/ubuntu")
from li_detail import fetch, extract

ids = ["4477695667", "4460636251", "4476996899", "4474140154", "4481725847",
       "4475615166", "4479689862", "4482493432", "4475432780", "4482876777",
       "4470998122", "4470521160", "4464042483", "4474168352"]
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
with open("/home/ubuntu/li_details3.json", "w") as f:
    json.dump(out, f, indent=1)
print("saved", len(out))
