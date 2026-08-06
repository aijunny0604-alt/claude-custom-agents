# -*- coding: utf-8 -*-
"""네이버 검색광고 입찰 최적화.
analyze: 계획 산출. apply_down: 낮춤(과지출 절감)만 반영. apply_up_safe: 상한(800) 소폭 상향만. apply: 전체."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
CEIL_UP=800
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def call(method,uri,params=None,body=None):
    ts=str(int(time.time()*1000)); url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method)
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,method,uri))
    if data is not None: r.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(r,timeout=40) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e: return e.code,{"_err":e.read().decode("utf-8","ignore")[:200]}
def estimate_map(keywords, position, device):
    out={}
    for i in range(0,len(keywords),40):
        st,res=call("POST","/estimate/average-position-bid/keyword",body={"device":device,"items":[{"key":k,"position":position} for k in keywords[i:i+40]]})
        if st==200:
            for e in res.get("estimate",[]): out[e.get("keyword")]=e.get("bid")
        time.sleep(0.15)
    return out
def do_apply(items):
    done=0; delta=0
    for p in items:
        st,res=call("PUT","/ncc/keywords/"+p["id"],params={"fields":"bidAmt"},body={"nccKeywordId":p["id"],"nccAdgroupId":p["ag"],"bidAmt":p["rec"],"useGroupBidAmt":False})
        if 200<=st<300: done+=1; delta+=p["rec"]-p["cur"]
        else: print("실패",p["kw"],st,str(res.get("_err",""))[:60])
        time.sleep(0.1)
    return done,delta
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "analyze"
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    targets=[]
    for c in audit["campaigns"]:
        if c["status"]!="ELIGIBLE": continue
        dev="MOBILE" if c["name"]=="모바일" else "PC"
        for a in c["adgroups"]:
            if a["status"]!="ELIGIBLE": continue
            for k in a["keywords"]:
                if k.get("useGroupBid"): continue
                b=k.get("bidAmt")
                if isinstance(b,int) and b>=300 and k.get("kw") and k.get("nccKeywordId"):
                    targets.append({"id":k["nccKeywordId"],"ag":a["id"],"kw":k["kw"],"cur":b,"device":dev})
    plan=[]
    for dev in ("PC","MOBILE"):
        kws=sorted({t["kw"] for t in targets if t["device"]==dev})
        if not kws: continue
        est1=estimate_map(kws,1,dev)
        for t in [x for x in targets if x["device"]==dev]:
            e=est1.get(t["kw"])
            if not e: continue
            cur=t["cur"]; rec=cur
            if cur<e: rec=e
            elif cur>int(e*1.3): rec=max(e,100)
            if rec!=cur: plan.append({"id":t["id"],"ag":t["ag"],"kw":t["kw"],"dev":dev,"cur":cur,"rec":int(rec)})
    io.open("C:/tmp/ad_bid_plan.json","w",encoding="utf-8").write(json.dumps(plan,ensure_ascii=False))
    up=[p for p in plan if p["rec"]>p["cur"]]; down=[p for p in plan if p["rec"]<p["cur"]]
    print("analyze: 대상",len(targets),"조정",len(plan),"(올림",len(up),"낮춤",len(down),")")
    if mode=="apply_down":
        d,s=do_apply(down); print("apply_down 완료",d,"/",len(down),"· 절감합 -",s)
    elif mode=="apply_up_safe":
        safe=[{**q,"rec":min(q["rec"],CEIL_UP)} for q in up if min(q["rec"],CEIL_UP)>q["cur"]]
        d,s=do_apply(safe); print("apply_up_safe 완료",d,"/",len(safe),"· 상향합 +",s,"(상한",CEIL_UP,")")
    elif mode=="apply":
        d,s=do_apply(plan); print("apply 완료",d,"/",len(plan))
