# -*- coding: utf-8 -*-
"""그룹 키워드별 성과(노출·클릭·비용) 조회 — id단건 /stats 반복(90일). 결과 C:/tmp/kwstats.json."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
CAMP=sys.argv[1] if len(sys.argv)>1 else "모바일"; GROUP=sys.argv[2] if len(sys.argv)>2 else "흡배기튜닝"
SINCE="2026-05-08"; UNTIL="2026-08-06"; F=["impCnt","clkCnt","salesAmt"]
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def get(uri,params):
    ts=str(int(time.time()*1000)); url=BASE+uri+"?"+urllib.parse.urlencode(params)
    r=urllib.request.Request(url,method="GET")
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,"GET",uri))
    try:
        with urllib.request.urlopen(r,timeout=20) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e: return e.code,{}
    except Exception: return 0,{}
audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
gid=None
for c in audit["campaigns"]:
    if c["name"]==CAMP:
        for a in c["adgroups"]:
            if a["status"]=="ELIGIBLE" and a["name"].startswith(GROUP): gid=a["id"]
st,kws=get("/ncc/keywords",{"nccAdgroupId":gid})
items=[{"id":k["nccKeywordId"],"kw":k["keyword"],"bid":k.get("bidAmt")} for k in kws if k.get("keyword")]
print("그룹",gid,"키워드",len(items),"— 성과 조회 시작")
res=[]
for i,it in enumerate(items):
    st,r=get("/stats",{"id":it["id"],"fields":json.dumps(F),"timeRange":json.dumps({"since":SINCE,"until":UNTIL})})
    imp=clk=cost=0
    for row in (r.get("data") or []):
        imp+=row.get("impCnt") or 0; clk+=row.get("clkCnt") or 0; cost+=row.get("salesAmt") or 0
    res.append({**it,"imp":imp,"clk":clk,"cost":int(cost)})
    if (i+1)%150==0: print("  ",i+1,"/",len(items))
    time.sleep(0.02)
json.dump({"gid":gid,"group":GROUP,"since":SINCE,"until":UNTIL,"keywords":res},io.open("C:/tmp/kwstats.json","w",encoding="utf-8"),ensure_ascii=False)
dead=[x for x in res if x["imp"]==0]
waste=[x for x in res if x["cost"]>1000 and x["clk"]==0]
top=sorted(res,key=lambda x:-x["clk"])[:5]
print("완료 |","죽은키워드(노출0):",len(dead),"| 낭비(비용>1000·클릭0):",len(waste))
print("합계 노출",sum(x['imp'] for x in res),"클릭",sum(x['clk'] for x in res),"비용",sum(x['cost'] for x in res))
