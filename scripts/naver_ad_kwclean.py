# -*- coding: utf-8 -*-
"""그룹 키워드 검색량 조회 → 저검색(인기없음) 제거후보 + 고검색 추가후보 산출(읽기).
사용: python naver_ad_kwclean.py "모바일" "흡배기튜닝". 결과 C:/tmp/kwclean_plan.json + summary."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
CAMP=sys.argv[1] if len(sys.argv)>1 else "모바일"
GROUP=sys.argv[2] if len(sys.argv)>2 else "흡배기튜닝"
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def call(method,uri,params=None):
    ts=str(int(time.time()*1000)); url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    r=urllib.request.Request(url,method=method)
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,method,uri))
    try:
        with urllib.request.urlopen(r,timeout=30) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "[]")
    except urllib.error.HTTPError as e: return e.code,{"_err":e.read().decode("utf-8","ignore")[:150]}
def num(v):
    if isinstance(v,str): v=v.replace("<","").replace(",","").strip()
    try: return int(v)
    except: return 0
audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
gid=None
for c in audit["campaigns"]:
    if c["name"]==CAMP:
        for a in c["adgroups"]:
            if a["status"]=="ELIGIBLE" and a["name"].startswith(GROUP): gid=a["id"]
st,kws=call("GET","/ncc/keywords",{"nccAdgroupId":gid})
items=[{"id":k["nccKeywordId"],"kw":k["keyword"],"bid":k.get("bidAmt")} for k in kws if k.get("keyword")]
print("그룹",gid,"키워드",len(items))
# 검색량 조회 (keywordstool, 힌트 5개씩)
vol={}; rel_pool={}
kwlist=[it["kw"] for it in items]
for i in range(0,len(kwlist),5):
    chunk=kwlist[i:i+5]
    st,res=call("GET","/keywordstool",{"hintKeywords":",".join(x.replace(" ","") for x in chunk),"showDetail":"1"})
    if isinstance(res,dict):
        for r in res.get("keywordList",[]):
            t=r.get("relKeyword"); tot=num(r.get("monthlyPcQcCnt"))+num(r.get("monthlyMobileQcCnt"))
            rel_pool[t]=(tot,r.get("compIdx"))
    time.sleep(0.05)
# 기존 키워드 볼륨 매핑(공백제거 매칭)
def norm(s): return s.replace(" ","")
pooln={norm(k):v for k,v in rel_pool.items()}
LOWV=10
remove=[]; keep=[]
for it in items:
    v=pooln.get(norm(it["kw"]),(0,None))[0]
    it["vol"]=v
    (remove if v<LOWV else keep).append(it)
# 추가후보: rel_pool 중 고검색·미보유
have=set(norm(it["kw"]) for it in items)
add=[]
for k,(tot,comp) in rel_pool.items():
    if norm(k) in have: continue
    if tot>=500 and comp in ("낮음","중간"): add.append({"kw":k,"vol":tot,"comp":comp})
add=sorted(add,key=lambda x:-x["vol"])[:25]
json.dump({"gid":gid,"remove":remove,"add":add},io.open("C:/tmp/kwclean_plan.json","w",encoding="utf-8"),ensure_ascii=False)
L=[f"# {CAMP} > {GROUP} 키워드 정리 계획",
   f"기존 {len(items)} · 저검색(<{LOWV}) 제거후보 {len(remove)} · 유지 {len(keep)} · 추가후보 {len(add)}",
   "\n## 제거후보(인기없음) 예시 20",*[f"- {r['kw']} (검색 {r['vol']}, 입찰 {r['bid']})" for r in sorted(remove,key=lambda x:x['vol'])[:20]],
   "\n## 추가후보(고검색·저중경쟁) 상위",*[f"- {a['kw']} (검색 {a['vol']}, 경쟁 {a['comp']})" for a in add]]
io.open("C:/tmp/kwclean_summary.md","w",encoding="utf-8").write("\n".join(L))
print("완료: 제거후보",len(remove),"추가후보",len(add))
