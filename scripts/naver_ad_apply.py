# -*- coding: utf-8 -*-
"""네이버 검색광고 쓰기 — dedup(중복삭제) / addkw(키워드 추가).
dedup: C:/tmp/ad_dedup_plan.json 의 remove ids 삭제.
addkw: C:/tmp/ad_addkw.json = {campaign, group, bid, keywords[]} 를 해당 그룹에 추가."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def req(method,uri,params=None,body=None):
    ts=str(int(time.time()*1000)); url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method)
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,method,uri))
    if data is not None: r.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(r,timeout=40) as resp: return resp.status,(resp.read().decode("utf-8","ignore"))
    except urllib.error.HTTPError as e: return e.code,e.read().decode("utf-8","ignore")[:300]

mode = sys.argv[1] if len(sys.argv)>1 else "dedup"

if mode=="dedup":
    plan=json.load(io.open("C:/tmp/ad_dedup_plan.json",encoding="utf-8"))["plan"]
    ids=[r["id"] for p in plan for r in p["remove"]]
    print("삭제 대상",len(ids),"개")
    st,body=req("DELETE","/ncc/keywords",{"ids":ids[0]})
    print("테스트 삭제:",st,("OK" if 200<=st<300 else body))
    if not (200<=st<300): print("중단"); sys.exit(1)
    done=1
    for i in range(1,len(ids),15):
        st,body=req("DELETE","/ncc/keywords",{"ids":",".join(ids[i:i+15])})
        if 200<=st<300: done+=len(ids[i:i+15])
        else: print("배치실패",st,body[:100])
        time.sleep(0.2)
    print("삭제 완료",done,"/",len(ids))

elif mode=="addkw":
    cfg=json.load(io.open("C:/tmp/ad_addkw.json",encoding="utf-8"))
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    agid=None
    for c in audit["campaigns"]:
        if c["name"]!=cfg["campaign"]: continue
        for a in c["adgroups"]:
            if a["status"]=="ELIGIBLE" and a["name"].startswith(cfg["group"]): agid=a["id"]; break
    if not agid: print("그룹 못 찾음:",cfg["campaign"],cfg["group"]); sys.exit(1)
    print("대상 그룹:",agid)
    existing={k.get("kw") for c in audit["campaigns"] for a in c["adgroups"] if a["id"]==agid for k in a["keywords"]}
    body=[]
    for kw in cfg["keywords"]:
        if kw in existing: print("이미있음 스킵:",kw); continue
        body.append({"keyword":kw,"bidAmt":cfg.get("bid",500),"useGroupBidAmt":False})
    if not body: print("추가할 신규 키워드 없음"); sys.exit(0)
    st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":agid},body)
    if 200<=st<300:
        added=json.loads(resp) if resp.strip().startswith("[") else []
        print("추가 완료:",len(body),"개 요청 →",st)
        for x in ([a.get("keyword") for a in added] or [b["keyword"] for b in body]): print("  +",x)
    else:
        print("추가 실패",st,resp[:200])
