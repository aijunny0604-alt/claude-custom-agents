# -*- coding: utf-8 -*-
"""네이버 검색광고 쓰기 — dedup(중복삭제) / addkw(키워드 추가) / setup_tesla(전용그룹+소재 생성).
키는 ~/.secrets/naver_searchad.json 에서만 읽음."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
SITE_CH="bsn-a001-00-000000001599443"   # 무브모터스 블로그 SITE 채널
BLOG="https://blog.naver.com/move_am"
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def req(method,uri,params=None,body=None):
    ts=str(int(time.time()*1000)); url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    data=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(url,data=data,method=method)
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,method,uri))
    if data is not None: r.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(r,timeout=40) as resp: return resp.status,resp.read().decode("utf-8","ignore")
    except urllib.error.HTTPError as e: return e.code,e.read().decode("utf-8","ignore")[:400]
mode = sys.argv[1] if len(sys.argv)>1 else "dedup"

if mode=="dedup":
    plan=json.load(io.open("C:/tmp/ad_dedup_plan.json",encoding="utf-8"))["plan"]
    ids=[r["id"] for p in plan for r in p["remove"]]
    print("삭제 대상",len(ids))
    st,body=req("DELETE","/ncc/keywords",{"ids":ids[0]}); print("테스트:",st)
    if not (200<=st<300): print(body); sys.exit(1)
    done=1
    for i in range(1,len(ids),15):
        st,body=req("DELETE","/ncc/keywords",{"ids":",".join(ids[i:i+15])})
        if 200<=st<300: done+=len(ids[i:i+15])
        time.sleep(0.2)
    print("삭제 완료",done)

elif mode=="addkw":
    cfg=json.load(io.open("C:/tmp/ad_addkw.json",encoding="utf-8"))
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    agid=None
    for c in audit["campaigns"]:
        if c["name"]!=cfg["campaign"]: continue
        for a in c["adgroups"]:
            if a["status"]=="ELIGIBLE" and a["name"].startswith(cfg["group"]): agid=a["id"]
    body=[{"keyword":k,"bidAmt":cfg.get("bid",500),"useGroupBidAmt":False} for k in cfg["keywords"]]
    st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":agid},body)
    print("addkw",st,resp[:200])

elif mode=="setup_tesla":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    campid=None; etcgid=None
    for c in audit["campaigns"]:
        if c["name"]=="모바일":
            campid=c["id"]
            for a in c["adgroups"]:
                if a["status"]=="ELIGIBLE" and a["name"].startswith("기타 개조"): etcgid=a["id"]
    print("모바일 campaign:",campid,"| 기타개조 group:",etcgid)
    kws=["테슬라선쉐이드","테슬라썬쉐이드","모델Y선쉐이드","모델YL선쉐이드","전동선쉐이드","테슬라전동선쉐이드"]
    # 1) 그룹 생성
    grp_body={"nccCampaignId":campid,"adgroupType":"WEB_SITE","name":"테슬라 선쉐이드","pcChannelId":SITE_CH,"mobileChannelId":SITE_CH,
              "bidAmt":600,"useDailyBudget":False,"useKeywordPlus":True,"keywordPlusWeight":100,
              "mobileNetworkBidWeight":100,"pcNetworkBidWeight":100,"contentsNetworkBidAmt":None,"targets":[]}
    st,resp=req("POST","/ncc/adgroups",body=grp_body)
    print("그룹생성:",st)
    if not (200<=st<300): print("실패 본문:",resp); sys.exit(1)
    newg=json.loads(resp)["nccAdgroupId"]; print("새 그룹:",newg)
    # 2) 소재 생성
    ad_body={"nccAdgroupId":newg,"type":"TEXT_45","ad":{
        "headline":"{keyword:테슬라선쉐이드} 장착",
        "description":"부산 기장 정관 무브모터스 · 테슬라 전동 선쉐이드 전문점",
        "pc":{"final":BLOG,"display":BLOG},"mobile":{"final":BLOG,"display":BLOG}}}
    st,resp=req("POST","/ncc/ads",body=ad_body)
    print("소재생성:",st, "" if 200<=st<300 else resp[:300])
    # 3) 키워드 새 그룹에 추가
    kbody=[{"keyword":k,"bidAmt":600,"useGroupBidAmt":True} for k in kws]
    st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":newg},kbody)
    print("키워드추가:",st, "" if 200<=st<300 else resp[:300])
    # 4) 기타개조에서 같은 키워드 삭제
    st,kl=req("GET","/ncc/keywords",{"nccAdgroupId":etcgid})
    if 200<=st<300:
        arr=json.loads(kl); delids=[k["nccKeywordId"] for k in arr if k.get("keyword") in kws]
        if delids:
            st2,_=req("DELETE","/ncc/keywords",{"ids":",".join(delids)})
            print("기타개조서 삭제:",st2,len(delids),"개")
    print("완료: 테슬라 전용그룹",newg)

elif mode=="tesla_ad":
    g="grp-a001-01-000000071372927"
    ad_body={"nccAdgroupId":g,"type":"TEXT_45","ad":{
        "headline":"{keyword:테슬라선쉐이드} 장착",
        "description":"부산 기장 정관 무브모터스 테슬라 전동 선쉐이드 전문점",
        "pc":{"final":BLOG,"display":BLOG},"mobile":{"final":BLOG,"display":BLOG}}}
    st,resp=req("POST","/ncc/ads",body=ad_body)
    print("소재생성:",st, "OK" if 200<=st<300 else resp[:300])
