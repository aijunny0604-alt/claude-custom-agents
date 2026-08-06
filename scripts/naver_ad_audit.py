# -*- coding: utf-8 -*-
"""네이버 검색광고 계정 읽기 감사 — 캠페인/광고그룹/키워드(입찰가)/소재.
읽기 전용(GET). 결과 C:/tmp/naver_ad_audit.json (UTF-8). 쓰기 없음."""
import json, time, hmac, hashlib, base64, os, io
import urllib.request, urllib.parse, urllib.error

CFG = os.path.join(os.path.expanduser("~"), ".secrets", "naver_searchad.json")
BASE = "https://api.searchad.naver.com"
OUT = "C:/tmp/naver_ad_audit.json"

def load():
    with open(CFG, encoding="utf-8") as f: return json.load(f)
C = load()

def sign(ts, method, uri):
    msg = "{}.{}.{}".format(ts, method, uri)
    return base64.b64encode(hmac.new(C["SECRET_KEY"].encode(), msg.encode(), hashlib.sha256).digest()).decode()

def get(uri, params=None):
    ts = str(int(time.time()*1000))
    url = BASE + uri + (("?"+urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-Timestamp", ts); req.add_header("X-API-KEY", C["API_KEY"])
    req.add_header("X-Customer", str(C["CUSTOMER_ID"])); req.add_header("X-Signature", sign(ts,"GET",uri))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_msg": e.read().decode("utf-8","ignore")[:200]}

out = {"campaigns": []}
camps = get("/ncc/campaigns")
if isinstance(camps, dict) and camps.get("_error"):
    out["error"] = camps
else:
    for c in camps:
        cc = {"id": c.get("nccCampaignId"), "name": c.get("name"), "type": c.get("campaignTp"),
              "status": c.get("status"), "delivery": c.get("deliveryMethod"),
              "dailyBudget": c.get("dailyBudget"), "adgroups": []}
        ags = get("/ncc/adgroups", {"nccCampaignId": c.get("nccCampaignId")})
        if isinstance(ags, list):
            for a in ags:
                ag = {"id": a.get("nccAdgroupId"), "name": a.get("name"), "status": a.get("status"),
                      "bidAmt": a.get("bidAmt"), "dailyBudget": a.get("dailyBudget"),
                      "useDailyBudget": a.get("useDailyBudget"), "keywords": [], "ads": []}
                kws = get("/ncc/keywords", {"nccAdgroupId": a.get("nccAdgroupId")})
                if isinstance(kws, list):
                    for k in kws:
                        ag["keywords"].append({"kw": k.get("keyword"), "bidAmt": k.get("bidAmt"),
                            "useGroupBid": k.get("useGroupBidAmt"), "status": k.get("status"),
                            "nccKeywordId": k.get("nccKeywordId")})
                ads = get("/ncc/ads", {"nccAdgroupId": a.get("nccAdgroupId")})
                if isinstance(ads, list):
                    for ad in ads:
                        ag["ads"].append({"type": ad.get("type"), "status": ad.get("status"), "ad": ad.get("ad")})
                cc["adgroups"].append(ag)
        out["campaigns"].append(cc)

with io.open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
nc = len(out.get("campaigns", []))
ng = sum(len(c["adgroups"]) for c in out.get("campaigns", []))
nk = sum(len(a["keywords"]) for c in out.get("campaigns", []) for a in c["adgroups"])
print("OK", OUT, "| campaigns", nc, "adgroups", ng, "keywords", nk, "| err", "error" in out)
