#!/usr/bin/env python3
"""Read-only first-party NBA season schedule and boxscore probe; no guesses published."""
import json,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone

urls={
"schedule_cdn_v1":"https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
"schedule_cdn":"https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
"schedule_nba_s3":"https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/static/json/staticData/scheduleLeagueV2_1.json",
"schedule_mobile":"https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2026/league/00_full_schedule.json",
"schedule_teams":"https://www.nba.com/schedule",
"boxscore_s3_ind_phi":"https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_0022600236.json",
"boxscore_s3_first":"https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_0022600001.json",
"boxscore_cdn_ind_phi":"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022600236.json",
}
status={}
for k,url in urls.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)","Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
  with urllib.request.urlopen(req,timeout=15) as r:
   raw=r.read(12_000_000)
   o={"status":r.status,"length":len(raw),"contentType":r.headers.get("Content-Type")}
  if raw[:1] in (b"{",b"["):
   data=json.loads(raw)
   o["rootKeys"]=list(data)[:16] if isinstance(data,dict) else ["list"]
   if k.startswith("schedule"): 
    league=data.get("leagueSchedule",{}) if isinstance(data,dict) else {}
    o["scheduleKeys"]=list(league)
    days=league.get("gameDates",[])
    o["days"]=len(days)
    o["firstDay"]=str(days[0])[:600] if days else None
   else:
    game=data.get("game",{})
    o["game"]={x:game.get(x) for x in ("gameId","gameStatus","gameStatusText","gameTimeUTC","gameEt","gameTimeLocal","gameLabel")}
    o["homeKeys"]=list(game.get("homeTeam",{}))[:25] if game.get("homeTeam") else []
    o["awayPlayers"]=len(game.get("awayTeam",{}).get("players",[]))
    o["onePlayer"]=str(game.get("awayTeam",{}).get("players",[{}])[0])[:1000]
  status[k]=o
 except (urllib.error.HTTPError,urllib.error.URLError,ValueError,OSError) as e:
  status[k]={"error":type(e).__name__,"detail":str(e)[:140]}
 print(k,status[k].get("status",status[k].get("error")),flush=True)
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/fullseason_probe.json").write_text(json.dumps({"checkedAtUtc":datetime.now(timezone.utc).isoformat(),"probes":status},indent=2)+"\n")
