# -*- coding: utf-8 -*-
"""읽기 — 비즈채널 목록 + 기존 소재(ad) 구조 샘플. 결과 C:/tmp/naver_ad_channels.json."""
import json, time, hmac, hashlib, base64, os, io
import urllib.request, urllib.parse, urllib.error
CFG=os.path.join(os.path.expanduser("~"),".secrets","naver_searchad.json")
BASE="https://api.searchad.naver.com"; C=json.load(open(CFG,encoding="utf-8"))
def sign(ts,m,uri): return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(),"{}.{}.{}".format(ts,m,uri).encode(),hashlib.sha256).digest()).decode()
def get(uri,params=None):
    ts=str(int(time.time()*1000)); url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    r=urllib.request.Request(url,method="GET")
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"]); r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,"GET",uri))
    try:
        with urllib.request.urlopen(r,timeout=40) as resp: return resp.status,json.loads(resp.read().decode("utf-8") or "[]")
    except urllib.error.HTTPError as e: return e.code,{"_err":e.read().decode("utf-8","ignore")[:300]}
st,ch=get("/ncc/channels",{"recordSize":"100"})
out={"channels_status":st,"channels":[]}
if isinstance(ch,list):
    for c in ch:
        out["channels"].append({"id":c.get("nccBusinessChannelId"),"tp":c.get("channelTp"),"name":c.get("name"),"url":c.get("channelKey") or c.get("url"),"status":c.get("status")})
else: out["channels_err"]=ch
# 기존 소재 하나 가져와 구조 확인 (기타 개조 그룹의 광고)
audit=json.load(io.open("C:/tmp/naver_ad_audit.json",encoding="utf-8"))
gid=None
for c in audit["campaigns"]:
    if c["name"]=="모바일":
        for a in c["adgroups"]:
            if a["status"]=="ELIGIBLE" and a["name"].startswith("기타 개조"): gid=a["id"]
st2,ads=get("/ncc/ads",{"nccAdgroupId":gid})
out["sample_group"]=gid
out["sample_ads"]=ads if isinstance(ads,list) else [ads]
io.open("C:/tmp/naver_ad_channels.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
print("channels:",st,"count",len(out["channels"]))
for c in out["channels"]: print("  ",c["tp"],c["id"],c["name"],c["url"])
print("sample ads status",st2,"count",len(out["sample_ads"]))
