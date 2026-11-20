#!/usr/bin/env python3
"""Test documented public API endpoints for free current 2026-27 NBA ratings.
No scraping of sites that prohibit bulk page reuse.
"""
import json,urllib.request,urllib.error
from urllib.parse import urlencode
from pathlib import Path
from datetime import datetime,timezone
base="https://api.pbpstats.com/get-all-season-stats/nba?"
qs={
 "pbp_player":dict(Season="2026-27",SeasonType="Regular Season",EntityType="Player"),
 "pbp_team":dict(Season="2026-27",SeasonType="Regular Season",EntityType="Team"),
 "pbp_single":dict(Season="2026-27",SeasonType="Regular Season",EntityType="Player",EntityId="1628973"),
}
urls={k:base+urlencode(v) for k,v in qs.items()}
urls.update({
 "hoopsnightly_open":"https://hoopsnightly.com/api/open",
 "hoopsnightly_open_teams":"https://hoopsnightly.com/api/open?dataset=team-stats",
 "hoopsnightly_open_stats":"https://hoopsnightly.com/api/open?type=teams",
 "pbp_docs":"https://api.pbpstats.com/openapi.json"
})
out={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"sources":{}}
for key,url in urls.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public research data feed audit)","Accept":"application/json,text/html;q=0.9"})
  with urllib.request.urlopen(req,timeout=14) as r:
   raw=r.read(1_800_001)
   typ=r.headers.get("Content-Type","")
   http=r.status
  res={"status":http,"contentType":typ,"size":len(raw)}
  if len(raw)>1_800_000:res["oversized"]=True
  try:
   val=json.loads(raw)
   res["topKeys"]=list(val)[:28] if isinstance(val,dict) else ["list"]
   if isinstance(val,list):res["n"]=len(val)
   if isinstance(val,dict):
    for field in ("multi_row_table_data","results","data","headers","players","teams"):
     v=val.get(field)
     if isinstance(v,list):
      res[field+"_count"]=len(v)
      res[field+"_sample"]=str(v[0])[:750] if v else ""
     if isinstance(v,dict):
      res[field+"_keys"]=list(v)[:20]
      res[field+"_sample"]=str(next(iter(v.values()),""))[:400]
  except ValueError:res["htmlSample"]=raw[:200].decode("utf8","replace")
  out["sources"][key]=res
 except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,TimeoutError) as e:
  out["sources"][key]={"error":f"{type(e).__name__}: {str(e)[:150]}"}
 print(key,out["sources"][key].get("status",out["sources"][key].get("error")),flush=True)
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/ratings_api_probe.json").write_text(json.dumps(out,indent=2)+"\n")
