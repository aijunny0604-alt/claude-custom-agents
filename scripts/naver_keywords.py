# -*- coding: utf-8 -*-
"""네이버 검색광고 키워드도구 조회 — 연관키워드+월검색량+경쟁도+파워링크 평균노출광고수.
사용: python naver_keywords.py "키워드1" "키워드2" ...  (공백 자동제거, 최대 5개 힌트)
키: ~/.secrets/naver_searchad.json (API_KEY, SECRET_KEY, CUSTOMER_ID)
결과: C:/tmp/naver_kw_result.json (UTF-8) 저장 + 콘솔 요약. 분석은 이 JSON을 Read.
"""
import sys, os, json, time, hmac, hashlib, base64, io
import urllib.request, urllib.parse, urllib.error

CFG = os.path.join(os.path.expanduser("~"), ".secrets", "naver_searchad.json")
BASE = "https://api.searchad.naver.com"
# 출력 경로: 환경변수 NAVER_KW_OUT > 기본값. 🚨 병렬 실행(에이전트 여러 개) 시
# 기본 경로를 서로 덮어쓰므로 각자 고유 경로를 NAVER_KW_OUT 로 지정할 것.
OUT = os.environ.get("NAVER_KW_OUT") or "C:/tmp/naver_kw_result.json"

def load():
    with open(CFG, encoding="utf-8") as f:
        return json.load(f)

def sign(secret, ts, method, uri):
    msg = "{}.{}.{}".format(ts, method, uri)
    d = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(d).decode("utf-8")

def keywordstool(hints):
    c = load()
    uri = "/keywordstool"
    ts = str(int(time.time() * 1000))
    sig = sign(c["SECRET_KEY"], ts, "GET", uri)
    hint = ",".join(h.replace(" ", "") for h in hints)[:200]
    qs = urllib.parse.urlencode({"hintKeywords": hint, "showDetail": "1"})
    req = urllib.request.Request(BASE + uri + "?" + qs, method="GET")
    req.add_header("X-Timestamp", ts)
    req.add_header("X-API-KEY", c["API_KEY"])
    req.add_header("X-Customer", str(c["CUSTOMER_ID"]))
    req.add_header("X-Signature", sig)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def num(v):
    if isinstance(v, str):
        v = v.replace("<", "").replace(",", "").strip()
        try: return int(v)
        except: return 0
    return v or 0

if __name__ == "__main__":
    hints = sys.argv[1:]
    if not hints:
        print("사용: python naver_keywords.py \"키워드\" ..."); sys.exit(1)
    try:
        data = keywordstool(hints)
    except urllib.error.HTTPError as e:
        print("HTTP 오류", e.code, e.read().decode("utf-8", "ignore")); sys.exit(1)
    rows = data.get("keywordList", [])
    for k in rows:
        k["_total"] = num(k.get("monthlyPcQcCnt")) + num(k.get("monthlyMobileQcCnt"))
    rows.sort(key=lambda x: x["_total"], reverse=True)
    slim = [{"kw": k.get("relKeyword"), "pc": num(k.get("monthlyPcQcCnt")),
             "mo": num(k.get("monthlyMobileQcCnt")), "total": k["_total"],
             "comp": k.get("compIdx"), "pl": k.get("plAvgDepth")} for k in rows]
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump({"hints": hints, "count": len(rows), "keywords": slim}, f, ensure_ascii=False, indent=1)
    print("OK saved:", OUT, "| keywords:", len(rows))
