import sys, json, time
sys.path.insert(0, "/home/ubuntu")
from li_detail import fetch, extract

ids = ["4456184752", "4474993966", "4430002565", "4464872919", "4472154058",
       "4477668218", "4472586663", "4472807657", "4479002027", "4478993949",
       "4443795362", "4478113995", "4480361850", "4466306538", "4476493614",
       "4474098218", "4474141243", "4467630203"]
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
with open("/home/ubuntu/li_details2.json", "w") as f:
    json.dump(out, f, indent=1)
print("saved", len(out))
