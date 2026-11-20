#!/usr/bin/env python3
"""Inspect official PBP Stats API schema and exact response field names, no writes beyond probe."""
import json,urllib.request,urllib.error
from urllib.parse import urlencode
from pathlib import Path
from datetime import datetime,timezone
def get(u):
 req=urllib.request.Request(u,headers={"User-Agent":"SportsBobResearch/0.1 (+free advanced stats pilot)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=15) as resp:return json.loads(resp.read(1_600_000))
out={"checkedAtUtc":datetime.now(timezone.utc).isoformat(),"schema":{},"sample":{}}
try:
 api=get("https://api.pbpstats.com/openapi.json")
 out["onoff_enum"]=api.get("components",{}).get("schemas",{}).get("OnOffStatTypeEnum",{})
 for k,v in api.get("paths",{}).items():
  if any(x in k for x in ["get-on-off","get-all-season-stats","get-team-players-for-season"]):
   ep=v.get("get",{})
   out["schema"][k]={"summary":ep.get("summary"),"description":str(ep.get("description"))[:400],
      "params":[{"name":p.get("name"),"required":p.get("required"),"type":p.get("schema"),"description":str(p.get("description"))[:90]} for p in ep.get("parameters",[])],
      "requestSchema":ep.get("requestBody",{})}
except Exception as e:out["schemaError"]=str(e)
api_urls={
 "single_brunson":"https://api.pbpstats.com/get-all-season-stats/nba?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","EntityType":"Player","EntityId":"1628973"}),
 "team_nyk":"https://api.pbpstats.com/get-all-season-stats/nba?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","EntityType":"Team","EntityId":"1610612752"}),
 "onoff_nyk":"https://api.pbpstats.com/get-on-off/nba?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752"}),
 "hoopsnightly_open":"https://hoopsnightly.com/api/open",
 "hoopsnightly_onoff":"https://hoopsnightly.com/api/open?part=on-off",
 "onoff_stat_offrating":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"OffRtg"}),
 "onoff_stat_defrating":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"DefRtg"}),
 "onoff_stat_points100":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"PtsPer100Poss"}),
 "onoff_stat_opp100":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"OppPtsPer100Poss"}),
 "onoff_stat_opponentpoints":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"OpponentPtsPer100Poss"}),
 "onoff_stat_net":"https://api.pbpstats.com/get-on-off/nba/stat?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","Stat":"OnNetRtg"}),
 "onoff_player_brunson":"https://api.pbpstats.com/get-on-off/nba/player?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","PlayerId":"1628973"}),
 "onoff_team_brunson":"https://api.pbpstats.com/get-on-off/nba/team?"+urlencode({"Season":"2026-27","SeasonType":"Regular Season","TeamId":"1610612752","PlayerId":"1628973"})
}
for key,url in api_urls.items():
 try:
  data=get(url)
  r={"rootKeys":list(data)[:20] if isinstance(data,dict) else [],
     "rawType":type(data).__name__}
  if key in ("hoopsnightly_open","hoopsnightly_onoff"):r["payload"]=str(data)[:1000]
  if key=="onoff_player_brunson":
   options=data.get("stat_options",{})
   r["ratingFields"]=[v for v in options.get("data",[]) if any(w in str(v).lower() for w in ("per100","rating","rtg","opp","points","poss"))]

  if key=="single_brunson":
   reg=data.get("results",{}).get("Regular Season",[])
   latest=[x for x in reg if x.get("Season")=="2026-27"]
   r["recentSeasonRows"]=len(latest);r["recentSeasonKeys"]=list(latest[0])[:100] if latest else []
   r["ratingsCandidateFields"]={k:v for k,v in (latest[0].items() if latest else []) if any(t in k.lower() for t in ["rating","poss","offensive","defensive","net"])}
  if key=="team_nyk":
   r["resultsType"]=type(data.get("results")).__name__;r["resultsKeys"]=list(data.get("results",{}))[:20]
   reg=data.get("results",{}).get("Regular Season",[])
   latest=[x for x in reg if x.get("Season")=="2026-27"]
   r["currentRowRatingKeys"]={k:v for k,v in (latest[0].items() if latest else []) if any(word in k.lower() for word in ("rating","rtg","poss","point","net"))}
  if key in ("onoff_nyk","onoff_stat_net","onoff_stat_offrating","onoff_stat_defrating","onoff_stat_points100","onoff_stat_opp100","onoff_stat_opponentpoints","onoff_player_brunson","onoff_team_brunson"):
   r["keys"]=list(data)[:30]
   r["sample"]={k:(str(v)[:700] if isinstance(v,(dict,list)) else str(v)[:120]) for k,v in list(data.items())[:6]}
  out["sample"][key]=r
 except Exception as e:out["sample"][key]={"error":f"{type(e).__name__}: {str(e)[:140]}"}
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/pbp_schema_probe.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"schema":out.get("schema"),"samples":out["sample"]},indent=2))
