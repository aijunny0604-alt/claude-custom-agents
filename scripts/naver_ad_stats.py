# -*- coding: utf-8 -*-
"""네이버 검색광고 성과 조회(읽기). diag: 형식 진단. run: 성과 수집→C:/tmp/naver_ad_stats.json."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def get(uri,params):
    ts=str(int(time.time()*1000)); url=BASE+uri+"?"+urllib.parse.urlencode(params)
    r=urllib.request.Request(url,method="GET")
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,"GET",uri))
    try:
        with urllib.request.urlopen(r,timeout=60) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e: return e.code,{"_err":e.read().decode("utf-8","ignore")[:300]}
audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
camps={c["id"]:c["name"] for c in audit["campaigns"]}
groups={a["id"]:(c["name"],a["name"]) for c in audit["campaigns"] for a in c["adgroups"]}
FIELDS=["impCnt","clkCnt","salesAmt","ctr","cpc","ccnt"]
SINCE=sys.argv[2] if len(sys.argv)>2 else "2026-05-01"
UNTIL=sys.argv[3] if len(sys.argv)>3 else "2026-08-06"
mode=sys.argv[1] if len(sys.argv)>1 else "diag"
cid=list(camps)[0]
if mode=="diag":
    print("첫 캠페인:",cid)
    variants=[
      ("id+timeRange",{"id":cid,"fields":json.dumps(FIELDS),"timeRange":json.dumps({"since":SINCE,"until":UNTIL})}),
      ("id+datePreset",{"id":cid,"fields":json.dumps(FIELDS),"datePreset":"last30days"}),
      ("ids+datePreset",{"ids":json.dumps([cid]),"fields":json.dumps(FIELDS),"datePreset":"last30days"}),
      ("id+timeRange+incr",{"id":cid,"fields":json.dumps(FIELDS),"timeRange":json.dumps({"since":SINCE,"until":UNTIL}),"timeIncrement":"allDays"}),
    ]
    for name,p in variants:
        st,res=get("/stats",p)
        print(f"[{name}] {st} {json.dumps(res,ensure_ascii=False)[:200]}")
elif mode=="run":
    # id 단건, 92일 이내, 일별 rows 합산
    def summ(entity_id):
        st,res=get("/stats",{"id":entity_id,"fields":json.dumps(FIELDS),"timeRange":json.dumps({"since":SINCE,"until":UNTIL})})
        rows=res.get("data") if isinstance(res,dict) else None
        agg={"impCnt":0,"clkCnt":0,"salesAmt":0,"ccnt":0}
        for r in (rows or []):
            for k in agg: agg[k]+=(r.get(k) or 0)
        agg["ctr"]=round(agg["clkCnt"]/agg["impCnt"]*100,2) if agg["impCnt"] else 0
        agg["cpc"]=int(agg["salesAmt"]/agg["clkCnt"]) if agg["clkCnt"] else 0
        return agg
    out={"since":SINCE,"until":UNTIL,"campaigns":[],"adgroups":[]}
    for cid,cn in camps.items():
        row=summ(cid); row["name"]=cn; row["id"]=cid; out["campaigns"].append(row); time.sleep(0.13)
    for gid,(cn,an) in groups.items():
        row=summ(gid); row["camp"]=cn; row["name"]=an; row["id"]=gid; out["adgroups"].append(row); time.sleep(0.11)
    io.open("C:/tmp/naver_ad_stats.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    t=lambda f: sum((r.get(f) or 0) for r in out["campaigns"])
    print("기간",SINCE,"~",UNTIL,"| 합계  노출",t("impCnt"),"클릭",t("clkCnt"),"비용",int(t("salesAmt")),"전환",t("ccnt"))
    print("데이터 있는 캠페인:",sum(1 for r in out["campaigns"] if (r.get("impCnt") or 0)>0),"/",len(out["campaigns"]))
