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

elif mode=="set_budget":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    # 성과기반 배분 (합계 49,000 ≤ 5만원)
    rules=[("모바일",30000),("자동차 정비",8000),("구조변경",5000),("보험",2000),("무브모터스",4000)]
    def budget_for(name):
        if name=="모바일": return 35000
        if name=="자동차 정비": return 9000
        if "구조변경" in name: return 7000
        if "보험" in name: return 4000
        if "무브모터스" in name: return 5000   # 플레이스
        return None
    done=0; tot=0
    for c in audit["campaigns"]:
        b=budget_for(c["name"])
        if b is None: continue
        st,resp=req("PUT","/ncc/campaigns/"+c["id"],{"fields":"budget"},{"nccCampaignId":c["id"],"dailyBudget":b,"useDailyBudget":True})
        ok=200<=st<300
        print(("OK " if ok else "실패 ")+c["name"]+" → "+str(b), st, "" if ok else resp[:150])
        if ok: done+=1; tot+=b
        time.sleep(0.15)
    print("일예산 설정 완료",done,"캠페인 · 합계",tot,"원/일")

elif mode=="addbulk":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    cfg=json.load(io.open("C:/tmp/addbulk_config.json",encoding="utf-8"))
    REGIONS=["부산","울산","김해","양산","창원","기장","정관","경남"]
    grand=0
    for job in cfg:
        gid=None
        for c in audit["campaigns"]:
            if c["name"]==job["campaign"]:
                for a in c["adgroups"]:
                    if a["status"]=="ELIGIBLE" and a["name"].startswith(job["group"]): gid=a["id"]
        if not gid: print("그룹없음:",job["campaign"],job["group"]); continue
        st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":gid})
        try: existing=set(k["keyword"].replace(" ","") for k in json.loads(kt))
        except: existing=set()
        cands=[]
        for t in job["terms"]:
            cands.append(t)
            for r in REGIONS: cands.append(r+t)
        new=[k for k in dict.fromkeys(cands) if k.replace(" ","") not in existing]
        if not new: print(job["group"],"추가0(전부기존)"); continue
        body=[{"keyword":k,"bidAmt":job.get("bid",250),"useGroupBidAmt":False} for k in new]
        added=0
        for i in range(0,len(body),90):
            st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":gid},body[i:i+90])
            if 200<=st<300: added+=len(body[i:i+90])
            else: print("  실패",job["group"],st,resp[:90])
            time.sleep(0.2)
        grand+=added; print("OK",job["campaign"],">",job["group"],"추가",added,"/",len(new))
    print("== 총 추가",grand,"개 ==")

elif mode=="setup_ev":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    campid=None
    for c in audit["campaigns"]:
        if c["name"]=="모바일": campid=c["id"]
    grp_body={"nccCampaignId":campid,"adgroupType":"WEB_SITE","name":"전기차 튜닝 악세사리","pcChannelId":SITE_CH,"mobileChannelId":SITE_CH,
              "bidAmt":300,"useDailyBudget":False,"useKeywordPlus":True,"keywordPlusWeight":100,"mobileNetworkBidWeight":100,"pcNetworkBidWeight":100,"targets":[]}
    st,resp=req("POST","/ncc/adgroups",body=grp_body)
    print("EV 그룹생성:",st)
    if not (200<=st<300): print(resp); sys.exit(1)
    newg=json.loads(resp)["nccAdgroupId"]; print("새 EV 그룹:",newg)
    ad_body={"nccAdgroupId":newg,"type":"TEXT_45","ad":{
        "headline":"{keyword:전기차튜닝} 전문점",
        "description":"부산 기장 정관 무브모터스 전기차 튜닝 악세사리 전문점",
        "pc":{"final":BLOG,"display":BLOG},"mobile":{"final":BLOG,"display":BLOG}}}
    st,resp=req("POST","/ncc/ads",body=ad_body); print("EV 소재:",st,"OK" if 200<=st<300 else resp[:200])
    ev=["전기차튜닝","전기차악세사리","전기차선쉐이드","전기차하체","전기차다운스프링","전기차휠","전기차인치업","전기차휠타이어",
        "아이오닉5N튜닝","아이오닉N튜닝","아이오닉5튜닝","아이오닉6튜닝","EV6튜닝","EV6악세사리","테슬라튜닝","테슬라악세사리",
        "모델Y튜닝","모델3튜닝","모델YL튜닝","아이오닉5선쉐이드","EV6선쉐이드","전기차언더커버",
        "부산전기차튜닝","울산전기차튜닝","부산테슬라튜닝","부산아이오닉튜닝","김해전기차튜닝","양산전기차튜닝"]
    body=[{"keyword":k,"bidAmt":300,"useGroupBidAmt":True} for k in ev]
    st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":newg},body); print("EV 키워드:",st,len(ev),"개","OK" if 200<=st<300 else resp[:200])
    print("완료 EV그룹",newg)

elif mode=="cleanup_structure":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    # 1) 꺼진 미러 캠페인 '자동차튜닝' 삭제
    for c in audit["campaigns"]:
        if c["name"]=="자동차튜닝" and c["status"]!="ELIGIBLE":
            st,resp=req("DELETE","/ncc/campaigns/"+c["id"])
            print("미러캠페인 삭제:",st, "OK" if 200<=st<300 else resp[:150])
    # 2) 모바일 그룹명 타임스탬프(-1702...) 제거
    renamed=0
    for c in audit["campaigns"]:
        if c["name"]=="모바일":
            for a in c["adgroups"]:
                nm=a["name"]
                if "-1702" in nm:
                    clean=nm.rsplit("-",1)[0].strip()
                    st,resp=req("PUT","/ncc/adgroups/"+a["id"],{"fields":"name"},{"nccAdgroupId":a["id"],"name":clean})
                    if 200<=st<300: renamed+=1; print("  이름정리:",nm,"->",clean)
                    else: print("  실패:",nm,st,resp[:90])
                    time.sleep(0.15)
    print("그룹 이름정리 완료",renamed,"개")

elif mode=="reinforce":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    cfg=json.load(io.open("C:/tmp/reinforce_config.json",encoding="utf-8"))
    def num(v):
        if isinstance(v,str): v=v.replace("<","").replace(",","").strip()
        try: return int(v)
        except: return 0
    grand=0
    for job in cfg:
        gid=None
        for c in audit["campaigns"]:
            if c["name"]==job.get("campaign","모바일"):
                for a in c["adgroups"]:
                    if a["status"]=="ELIGIBLE" and a["name"].startswith(job["g"]): gid=a["id"]
        if not gid: print("그룹없음",job["g"]); continue
        st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":gid})
        try: existing=set(k["keyword"].replace(" ","") for k in json.loads(kt))
        except: existing=set()
        st,res=req("GET","/keywordstool",{"hintKeywords":",".join(s.replace(" ","") for s in job["seeds"][:5]),"showDetail":"1"})
        rel=[]
        try:
            for r in json.loads(res).get("keywordList",[]):
                rel.append((r.get("relKeyword"),num(r.get("monthlyPcQcCnt"))+num(r.get("monthlyMobileQcCnt")),r.get("compIdx")))
        except: print("검색량조회 실패",job["g"],res[:80]); continue
        toks=[t.lower() for t in job["tok"]]
        cand=[(k,v,cp) for k,v,cp in rel if k and any(t in k.lower() for t in toks) and v>=300 and k.replace(" ","") not in existing]
        cand=sorted(cand,key=lambda x:-x[1])[:20]
        if not cand: print(job["g"],"인기어 추가 0(신규없음)"); continue
        body=[{"keyword":k,"bidAmt":job.get("bid",300),"useGroupBidAmt":False} for k,_,_ in cand]
        st,resp=req("POST","/ncc/keywords",{"nccAdgroupId":gid},body)
        if 200<=st<300:
            grand+=len(cand); print("OK",job["g"],"+",len(cand),"| 예:",", ".join(f"{k}({v})" for k,v,_ in cand[:5]))
        else: print("실패",job["g"],st,resp[:100])
        time.sleep(0.3)
    print("== 인기 키워드 총 추가",grand,"==")

elif mode=="setbid":
    audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
    plan=json.load(io.open("C:/tmp/setbid.json",encoding="utf-8"))
    for p in plan:
        gid=None
        for c in audit["campaigns"]:
            if c["name"]==p.get("campaign","모바일"):
                for a in c["adgroups"]:
                    if a["status"]=="ELIGIBLE" and a["name"].startswith(p["group"]): gid=a["id"]
        if not gid: print("그룹없음",p["group"]); continue
        st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":gid})
        found=False
        for k in (json.loads(kt) if kt.strip().startswith("[") else []):
            if k.get("keyword")==p["keyword"]:
                found=True
                st,resp=req("PUT","/ncc/keywords/"+k["nccKeywordId"],{"fields":"bidAmt"},{"nccKeywordId":k["nccKeywordId"],"nccAdgroupId":gid,"bidAmt":p["bid"],"useGroupBidAmt":False})
                print(("OK " if 200<=st<300 else "실패 ")+p["keyword"]+" → "+str(p["bid"]),st, "" if 200<=st<300 else resp[:100])
        if not found: print("키워드없음",p["keyword"])

elif mode=="enable_ad":
    # 지정 그룹의 PAUSED 소재를 모두 ELIGIBLE로 켠다 (userLock 해제)
    gid=sys.argv[2] if len(sys.argv)>2 else "grp-a001-01-000000039420456"
    st,at=req("GET","/ncc/ads",{"nccAdgroupId":gid})
    ads=json.loads(at) if at.strip().startswith("[") else []
    for a in ads:
        if a.get("status")=="PAUSED" or a.get("userLock")==True:
            aid=a["nccAdId"]
            st2,resp=req("PUT","/ncc/ads/"+aid,{"fields":"userLock"},{"nccAdId":aid,"nccAdgroupId":gid,"userLock":False})
            print(("OK 소재켬 " if 200<=st2<300 else "실패 ")+aid,st2, "" if 200<=st2<300 else resp[:150])
    print("완료: enable_ad", gid)

elif mode=="dupscan":
    # 계정 전체에서 여러 그룹에 중복 등록된 키워드를 찾아 리포트 (읽기 전용)
    st,ct=req("GET","/ncc/campaigns"); camps=json.loads(ct)
    from collections import defaultdict
    seen=defaultdict(list)
    for c in camps:
        st,gt=req("GET","/ncc/adgroups",{"nccCampaignId":c["nccCampaignId"]})
        for g in (json.loads(gt) if gt.strip().startswith("[") else []):
            st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":g["nccAdgroupId"]})
            for k in (json.loads(kt) if kt.strip().startswith("[") else []):
                onoff="ON" if (k.get("userLock")==False and k.get("status")=="ELIGIBLE") else "OFF"
                seen[k.get("keyword")].append({"id":k["nccKeywordId"],"camp":c.get("name"),"grp":g.get("name"),"onoff":onoff,"bid":k.get("bidAmt"),"status":k.get("status")})
    dups={kw:rows for kw,rows in seen.items() if len(rows)>1}
    out={"total_keywords":len(seen),"dup_count":len(dups),"dups":dups}
    io.open("C:/tmp/ad_dupscan.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    print(f"전체 고유 키워드 {len(seen)} / 중복 키워드 {len(dups)}종 → C:/tmp/ad_dupscan.json")
    for kw,rows in list(dups.items())[:30]:
        print("  ",kw,"→",", ".join(f"{r['grp']}({r['onoff']})" for r in rows))

elif mode=="add_ext":
    # C:/tmp/add_ext.json = {"ownerId":"grp-..","exts":[{"type":..,"adExtension":..}, ...]}
    cfg=json.load(io.open("C:/tmp/add_ext.json",encoding="utf-8"))
    owner=cfg["ownerId"]
    for e in cfg["exts"]:
        body={"ownerId":owner,"type":e["type"],"adExtension":e["adExtension"]}
        if e.get("pcMobileType"): body["pcMobileType"]=e["pcMobileType"]
        st,resp=req("POST","/ncc/ad-extensions",None,body)
        print(("OK 확장추가 " if 200<=st<300 else "실패 ")+e["type"],st, "" if 200<=st<300 else resp[:200])

elif mode=="set_delivery":
    # 모든 ELIGIBLE 캠페인의 예산배분을 ACCELERATED(조기소진=계속 노출)로 변경. 균등배분(STANDARD) 해제.
    st,ct=req("GET","/ncc/campaigns"); camps=json.loads(ct)
    for c in camps:
        if c.get("deliveryMethod")=="ACCELERATED":
            print("이미 조기소진:",c["name"]); continue
        c["deliveryMethod"]="ACCELERATED"
        st2,resp=req("PUT","/ncc/campaigns/"+c["nccCampaignId"],{"fields":"budget"},c)
        print(("OK 균등배분해제 " if 200<=st2<300 else "실패 ")+c["name"],st2, "" if 200<=st2<300 else resp[:200])
    print("완료: set_delivery(ACCELERATED)")

elif mode=="del_ext":
    # 지정 그룹의 확장소재 전부 삭제 (검수중이라 노출 막을 때 원복용). ownerId=argv[2]
    owner=sys.argv[2] if len(sys.argv)>2 else "grp-a001-01-000000071372927"
    st,et=req("GET","/ncc/ad-extensions",{"ownerId":owner})
    exts=json.loads(et) if et.strip().startswith("[") else []
    for e in exts:
        eid=e.get("nccAdExtensionId")
        if not eid: print("id없음",e.get("type")); continue
        st2,resp=req("DELETE","/ncc/ad-extensions",{"ids":eid})
        print(("OK 확장삭제 " if 200<=st2<300 else "실패 ")+str(e.get("type")),st2, "" if 200<=st2<300 else resp[:120])
    print("완료: del_ext", owner)

elif mode=="deadscan":
    # 계정 전체 키워드의 90일 노출수 + 등록일 수집 (읽기전용) → 죽은키워드 판별용
    import datetime
    st,ct=req("GET","/ncc/campaigns"); camps=json.loads(ct)
    rows=[]; n=0
    for c in camps:
        st,gt=req("GET","/ncc/adgroups",{"nccCampaignId":c["nccCampaignId"]})
        for g in (json.loads(gt) if gt.strip().startswith("[") else []):
            st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":g["nccAdgroupId"]})
            kws=json.loads(kt) if kt.strip().startswith("[") else []
            for k in kws:
                kid=k["nccKeywordId"]
                st2,stt=req("GET","/stats",{"id":kid,"fields":json.dumps(["impCnt","clkCnt"]),"timeRange":json.dumps({"since":"2026-05-12","until":"2026-08-10"})})
                imp=0;clk=0
                try:
                    dd=json.loads(stt).get("data") or []
                    imp=sum(x.get("impCnt",0) or 0 for x in dd); clk=sum(x.get("clkCnt",0) or 0 for x in dd)
                except: pass
                rows.append({"id":kid,"kw":k.get("keyword"),"camp":c.get("name"),"grp":g.get("name"),
                             "regTm":k.get("regTm"),"status":k.get("status"),"userLock":k.get("userLock"),
                             "bid":k.get("bidAmt"),"imp90":imp,"clk90":clk})
                n+=1
                if n%200==0:
                    io.open("C:/tmp/kw_dead_scan.json","w",encoding="utf-8").write(json.dumps(rows,ensure_ascii=False))
                    print(f"  ...{n}개 스캔",flush=True)
                time.sleep(0.03)
    io.open("C:/tmp/kw_dead_scan.json","w",encoding="utf-8").write(json.dumps(rows,ensure_ascii=False))
    dead=[r for r in rows if r["imp90"]==0]
    print(f"완료: 총 {n}개 스캔 / 90일 노출0(죽음) {len(dead)}개 → C:/tmp/kw_dead_scan.json")

elif mode=="bid_optimize":
    # bid_opt.json + bid_est.json → 최적 입찰 계획(C:/tmp/setbid_bulk.json). 적용 안 함(계산+요약만).
    rows=json.load(io.open("C:/tmp/bid_opt.json",encoding="utf-8"))
    est=json.load(io.open("C:/tmp/bid_est.json",encoding="utf-8"))
    FLOOR=70; CAP=int(sys.argv[2]) if len(sys.argv)>2 else 600; KEEP={"부산배기튜닝"}  # CAP 인자로 조정
    plan=[]; raise_n=lower_n=0
    for r in rows:
        kw=r["kw"]; cur=r.get("bid") or 0; imp=r.get("imp90") or 0; clk=r.get("clk90") or 0
        if kw in KEEP: continue
        new=cur
        if clk>0:
            if kw in est:
                pc=est[kw].get("PC") or 0; mo=est[kw].get("MOBILE") or 0
                vals=[v for v in (pc,mo) if v]
                target=round(sum(vals)/len(vals)) if vals else max(cur,CAP)
            else:
                target=CAP     # 성과키워드인데 예상가 없으면 상한으로 (상위노출 확보)
            new=max(FLOOR,min(CAP,max(target, cur)))     # 성과키워드는 현재보다 낮추지 않음
        elif imp>0 and clk==0:
            # 노출되는데 클릭0 = 낭비 → 낮춤(현재의 60%, 하한 100)
            new=max(100,round(cur*0.6)) if cur>200 else cur
        else:
            # 노출0 = 최소 유지
            new=cur if cur<=150 else 150
        if abs(new-cur)>=20:
            plan.append({"id":r["id"],"kw":kw,"grp":r["grp"],"old":cur,"new":new})
            if new>cur: raise_n+=1
            else: lower_n+=1
    io.open("C:/tmp/setbid_bulk.json","w",encoding="utf-8").write(json.dumps(plan,ensure_ascii=False))
    print("입찰 최적화 계획: %d건 변경 (상향 %d / 하향 %d) → C:/tmp/setbid_bulk.json" % (len(plan),raise_n,lower_n))
    ups=[p for p in plan if p["new"]>p["old"]][:6]; dns=[p for p in plan if p["new"]<p["old"]][:6]
    print("상향 예시:"); [print("  %s %d→%d" % (p["kw"],p["old"],p["new"])) for p in ups]
    print("하향 예시:"); [print("  %s %d→%d" % (p["kw"],p["old"],p["new"])) for p in dns]

elif mode=="setbid_bulk":
    # setbid_bulk.json의 {id,new}를 PUT으로 일괄 반영
    plan=json.load(io.open("C:/tmp/setbid_bulk.json",encoding="utf-8"))
    print("입찰 일괄 반영:",len(plan),"건")
    ok=0
    for p in plan:
        # 키워드의 그룹id 필요 → GET로 조회 없이 bid_opt에서 매핑
        pass
    # bid_opt.json에서 id→grp 매핑
    rows={r["id"]:r for r in json.load(io.open("C:/tmp/bid_opt.json",encoding="utf-8"))}
    gidmap={}
    st,ct=req("GET","/ncc/campaigns")
    for c in json.loads(ct):
        st,gt=req("GET","/ncc/adgroups",{"nccCampaignId":c["nccCampaignId"]})
        for g in (json.loads(gt) if gt.strip().startswith("[") else []): gidmap[g["name"]]=g["nccAdgroupId"]
    for p in plan:
        r=rows.get(p["id"]);
        if not r: continue
        gid=gidmap.get(r["grp"])
        if not gid: continue
        st2,resp=req("PUT","/ncc/keywords/"+p["id"],{"fields":"bidAmt"},{"nccKeywordId":p["id"],"nccAdgroupId":gid,"bidAmt":p["new"],"useGroupBidAmt":False})
        if 200<=st2<300: ok+=1
        else:
            if ok<3: print("실패",p["kw"],st2,resp[:80])
        if ok%100==0 and ok>0: print("  ...%d건 반영"%ok,flush=True)
        time.sleep(0.02)
    print("입찰 일괄 반영 완료: %d/%d" % (ok,len(plan)))

elif mode=="grp_top3":
    # 지정 그룹의 성과키워드(clk>0)를 3위권 예상입찰가로 상향. argv[2]=gid, argv[3]=cap(기본1500)
    gid=sys.argv[2]; CAP=int(sys.argv[3]) if len(sys.argv)>3 else 1500
    perf={}
    try:
        for r in json.load(io.open("C:/tmp/kw_dead_scan.json",encoding="utf-8")): perf[r["kw"]]=r["clk90"]
    except: pass
    st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":gid})
    kws=json.loads(kt)
    # 성과키워드: 90일 클릭>0 (또는 실데이터 없으면 노출로 판단은 생략)
    perfk=[k for k in kws if (perf.get(k["keyword"],0) or 0)>0]
    names=[k["keyword"] for k in perfk]
    print("성과 키워드 %d개 3위권 예상가 조회..." % len(names))
    estd={}
    def est(dev,items):
        s,r=req("POST","/estimate/average-position-bid/keyword",None,{"device":dev,"items":[{"key":it,"position":3} for it in items]})
        if 200<=s<300:
            for e in json.loads(r).get("estimate",[]): estd.setdefault(e.get("keyword"),{})[dev]=e.get("bid")
    for i in range(0,len(names),80):
        est("PC",names[i:i+80]); est("MOBILE",names[i:i+80]); time.sleep(0.1)
    done=0
    for k in perfk:
        kw=k["keyword"]; cur=k["bidAmt"]; d=estd.get(kw,{})
        vals=[v for v in (d.get("PC"),d.get("MOBILE")) if v]
        if not vals: continue
        new=max(cur,min(CAP,round(sum(vals)/len(vals))))
        new=int(round(new/10.0))*10   # 네이버 입찰가 10원 단위
        if new<=cur: continue
        s,r=req("PUT","/ncc/keywords/"+k["nccKeywordId"],{"fields":"bidAmt"},{"nccKeywordId":k["nccKeywordId"],"nccAdgroupId":gid,"bidAmt":new,"useGroupBidAmt":False})
        if 200<=s<300: done+=1; print("  OK %s %d→%d (PC%s/모%s)"%(kw,cur,new,d.get("PC"),d.get("MOBILE")))
        else: print("  실패 %s %s"%(kw,r[:60]))
        time.sleep(0.03)
    print("완료: %d개 3위권 상향" % done)

elif mode=="bid_estimate":
    # bid_opt.json의 성과키워드(clk>0)에 대해 PC/모바일 위치별 예상입찰가 배치조회 → bid_est.json
    rows=json.load(io.open("C:/tmp/bid_opt.json",encoding="utf-8"))
    perf=[r for r in rows if (r["clk90"] or 0)>0]
    pos=int(sys.argv[2]) if len(sys.argv)>2 else 3
    out={}
    def est(device, items):
        body={"device":device,"items":[{"key":it,"position":pos} for it in items]}
        st,resp=req("POST","/estimate/average-position-bid/keyword",None,body)
        if 200<=st<300:
            try:
                for e in json.loads(resp).get("estimate",[]):
                    out.setdefault(e.get("keyword"),{})[device]=e.get("bid")
            except: pass
        else:
            print("est실패",device,st,resp[:100])
    kws=[r["kw"] for r in perf]
    for i in range(0,len(kws),80):
        chunk=kws[i:i+80]
        est("PC",chunk); est("MOBILE",chunk); time.sleep(0.1)
    io.open("C:/tmp/bid_est.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False))
    print("예상입찰 조회 완료: %d개 키워드 (position %d) → C:/tmp/bid_est.json" % (len(out),pos))
    ex=list(out.items())[:5]
    for kw,d in ex: print("  %s: PC %s / 모바일 %s" % (kw,d.get("PC"),d.get("MOBILE")))

elif mode=="bid_scan":
    # 현재 전 키워드의 bid + 그룹 PC/모바일 가중치 수집 → kw_dead_scan 성과와 병합 → C:/tmp/bid_opt.json
    perf={}
    try:
        for r in json.load(io.open("C:/tmp/kw_dead_scan.json",encoding="utf-8")): perf[r["id"]]=(r["imp90"],r["clk90"])
    except: pass
    st,ct=req("GET","/ncc/campaigns"); camps=json.loads(ct)
    rows=[]
    for c in camps:
        if c.get("status")!="ELIGIBLE": continue
        st,gt=req("GET","/ncc/adgroups",{"nccCampaignId":c["nccCampaignId"]})
        for g in (json.loads(gt) if gt.strip().startswith("[") else []):
            pcw=g.get("pcNetworkBidWeight",100); mow=g.get("mobileNetworkBidWeight",100)
            st,kt=req("GET","/ncc/keywords",{"nccAdgroupId":g["nccAdgroupId"]})
            for k in (json.loads(kt) if kt.strip().startswith("[") else []):
                imp,clk=perf.get(k["nccKeywordId"],(None,None))
                rows.append({"id":k["nccKeywordId"],"kw":k.get("keyword"),"camp":c.get("name"),"grp":g.get("name"),
                             "bid":k.get("bidAmt"),"useGrpBid":k.get("useGroupBidAmt"),"pcw":pcw,"mow":mow,"imp90":imp,"clk90":clk})
    io.open("C:/tmp/bid_opt.json","w",encoding="utf-8").write(json.dumps(rows,ensure_ascii=False))
    perfk=[r for r in rows if (r["clk90"] or 0)>0]
    impk=[r for r in rows if (r["imp90"] or 0)>0 and (r["clk90"] or 0)==0]
    deadk=[r for r in rows if (r["imp90"] or 0)==0]
    print("전 키워드 %d → 클릭有(성과)%d / 노출만(클릭0)%d / 죽음(노출0)%d" % (len(rows),len(perfk),len(impk),len(deadk)))
    wts=sorted(set("%s(pc%s/mo%s)"%(r["grp"][:8],r["pcw"],r["mow"]) for r in rows))
    print("C:/tmp/bid_opt.json 저장. 그룹 PC/모바일 가중치: "+", ".join(wts[:8]))

elif mode=="dead_del_list":
    # kw_dead_scan.json에서 삭제대상(90일 노출0 AND cutoff 이전 등록) → delkw.json 생성 (읽기+파일쓰기, API호출 없음)
    cutoff=sys.argv[2] if len(sys.argv)>2 else "2026-08"
    rows=json.load(io.open("C:/tmp/kw_dead_scan.json",encoding="utf-8"))
    targets=[r for r in rows if r["imp90"]==0 and (r.get("regTm") or "")[:7] < cutoff]
    ids=[r["id"] for r in targets]
    io.open("C:/tmp/delkw.json","w",encoding="utf-8").write(json.dumps(ids,ensure_ascii=False))
    protect=[r for r in rows if r["imp90"]==0 and (r.get("regTm") or "")[:7]>=cutoff]
    print(f"삭제대상(죽음+{cutoff}이전): {len(ids)}개 / 보호(최근): {len(protect)}개 / 남는 키워드: {len(rows)-len(ids)}개")
    from collections import defaultdict
    g=defaultdict(int)
    for r in targets: g[r['grp']]+=1
    for grp,nn in sorted(g.items(),key=lambda x:-x[1])[:12]: print(f"  {grp[:20]:<21} {nn}개")

elif mode=="delkw":
    # C:/tmp/delkw.json = 삭제할 nccKeywordId 배열. (중복 정리용)
    ids=json.load(io.open("C:/tmp/delkw.json",encoding="utf-8"))
    print("삭제 대상 키워드",len(ids))
    for i in range(0,len(ids),10):
        st,body=req("DELETE","/ncc/keywords",{"ids":",".join(ids[i:i+10])})
        print(("OK " if 200<=st<300 else "실패 ")+str(ids[i:i+10]),st, "" if 200<=st<300 else body[:120])
        time.sleep(0.2)
    print("완료: delkw")
