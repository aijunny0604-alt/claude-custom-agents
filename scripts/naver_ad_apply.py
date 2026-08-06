# -*- coding: utf-8 -*-
"""네이버 검색광고 쓰기 반영 — 키워드 중복 제거(dedup). ids는 plan에서만. 안전: 1건 테스트 후 배치."""
import json, time, hmac, hashlib, base64, os, io, sys
import urllib.request, urllib.parse, urllib.error
CFG = os.path.join(os.path.expanduser("~"), ".secrets", "naver_searchad.json")
BASE = "https://api.searchad.naver.com"
C = json.load(open(CFG, encoding="utf-8"))
def sign(ts, m, uri):
    return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(), "{}.{}.{}".format(ts,m,uri).encode(), hashlib.sha256).digest()).decode()
def req(method, uri, params=None):
    ts=str(int(time.time()*1000))
    url=BASE+uri+(("?"+urllib.parse.urlencode(params)) if params else "")
    r=urllib.request.Request(url, method=method)
    r.add_header("X-Timestamp",ts); r.add_header("X-API-KEY",C["API_KEY"])
    r.add_header("X-Customer",str(C["CUSTOMER_ID"])); r.add_header("X-Signature",sign(ts,method,uri))
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8","ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","ignore")[:300]
plan = json.load(io.open("C:/tmp/ad_dedup_plan.json", encoding="utf-8"))["plan"]
ids = [r["id"] for p in plan for r in p["remove"]]
print("삭제 대상", len(ids), "개")
st, body = req("DELETE", "/ncc/keywords", {"ids": ids[0]})
print("테스트 삭제 상태:", st, ("OK" if 200<=st<300 else body))
if not (200<=st<300):
    print("중단: 쓰기 실패"); sys.exit(1)
done=1
rest=ids[1:]
for i in range(0, len(rest), 15):
    batch=rest[i:i+15]
    st,body=req("DELETE","/ncc/keywords",{"ids":",".join(batch)})
    if 200<=st<300: done+=len(batch)
    else: print("배치 실패", st, body[:120])
    time.sleep(0.2)
print("삭제 완료", done, "/", len(ids))
