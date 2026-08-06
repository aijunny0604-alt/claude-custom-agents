# -*- coding: utf-8 -*-
"""네이버 검색광고 성과 조회(읽기) — 캠페인/광고그룹 노출·클릭·비용·CTR·CPC·전환.
사용: python naver_ad_stats.py [since YYYY-MM-DD] [until YYYY-MM-DD]. 결과 C:/tmp/naver_ad_stats.json."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
SINCE=sys.argv[1] if len(sys.argv)>1 else "2026-07-07"
UNTIL=sys.argv[2] if len(sys.argv)>2 else "2026-08-06"
FIELDS=["impCnt","clkCnt","salesAmt","ctr","cpc","ccnt"]
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def get(uri,params):
    ts=str(int(time.time()*1000)); url=BASE+uri+"?"+urllib.parse.urlencode(params)
    r=urllib.request.Request(url,method="GET")
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,"GET",uri))
    try:
        with urllib.request.urlopen(r,timeout=60) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e: return e.code,{"_err":e.read().decode("utf-8","ignore")[:400]}
def stats(ids):
    p={"ids":json.dumps(ids),"fields":json.dumps(FIELDS),"timeRange":json.dumps({"since":SINCE,"until":UNTIL})}
    return get("/stats",p)
audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
camps={c["id"]:c["name"] for c in audit["campaigns"]}
groups={a["id"]:(c["name"],a["name"]) for c in audit["campaigns"] for a in c["adgroups"]}
out={"since":SINCE,"until":UNTIL,"campaigns":[],"adgroups":[]}
st,res=stats(list(camps))
print("campaign stats status:",st)
if st!=200:
    print("ERR:",res.get("_err"))
data=res.get("data") if isinstance(res,dict) else None
for row in (data or []):
    row["name"]=camps.get(row.get("id"),row.get("id")); out["campaigns"].append(row)
agids=list(groups)
for i in range(0,len(agids),20):
    st2,res2=stats(agids[i:i+20])
    for row in (res2.get("data") or []):
        cn,an=groups.get(row.get("id"),("",row.get("id"))); row["camp"]=cn; row["name"]=an; out["adgroups"].append(row)
    time.sleep(0.2)
io.open("C:/tmp/naver_ad_stats.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
tot=lambda f: sum((r.get(f) or 0) for r in out["campaigns"])
print("기간",SINCE,"~",UNTIL)
print("합계  노출",tot("impCnt"),"클릭",tot("clkCnt"),"비용",int(tot("salesAmt")),"전환",tot("ccnt"))
print("데이터 캠페인:",sum(1 for r in out['campaigns'] if (r.get('impCnt') or 0)>0),"/",len(out['campaigns']))
