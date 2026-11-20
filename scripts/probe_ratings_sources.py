#!/usr/bin/env python3
"""Probe actual COMPLETE current-season NBA team/player ratings data sources.
No synthetic ratings. Reports status, table coverage and sample headers only.
"""
import json,re,urllib.request,urllib.error,html
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

class Tables(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.tables=[];self.t=None;self.r=None;self.c=None;self.in_script=False;self.in_style=False
 def handle_starttag(self,tag,attrs):
  if tag=="script":self.in_script=True
  elif tag=="style":self.in_style=True
  if tag=="table":self.t=[]
  elif tag=="tr" and self.t is not None:self.r=[]
  elif tag in ("th","td") and self.r is not None:self.c=[]
 def handle_data(self,s):
  if self.c is not None and not self.in_script and not self.in_style:self.c.append(s.strip())
 def handle_endtag(self,tag):
  if tag=="script":self.in_script=False
  elif tag=="style":self.in_style=False
  if tag in ("th","td") and self.c is not None and self.r is not None:
   self.r.append(" ".join(x for x in self.c if x));self.c=None
  elif tag=="tr" and self.r is not None and self.t is not None:
   if self.r:self.t.append(self.r)
   self.r=None
  elif tag=="table" and self.t is not None:
   self.tables.append(self.t);self.t=None

sources={
 "nba_api_hub_teams":"https://api-hub.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season",
 "nba_api_hub_players":"https://api-hub.nba.com/stats/players/advanced?Season=2026-27&SeasonType=Regular%20Season",
 "nba_api_hub_team_players":"https://api-hub.nba.com/stats/team/1610612752/players-advanced?Season=2026-27",
 "nba_offense_defense_30":"https://www-ng.nba.com/stats/teams/offense-and-defense-ratings",
 "fox_teams":"https://www.foxsports.com/nba/team-stats?category=advanced&season=2026&seasonType=reg",
 "fox_players":"https://www.foxsports.com/nba/stats?category=advanced&season=2026&seasonType=reg",
 "basketball_reference_teams":"https://www.basketball-reference.com/leagues/NBA_2027.html",
 "basketball_reference_players":"https://www.basketball-reference.com/leagues/NBA_2027_advanced.html",
 "hoopsnightly_teams":"https://hoopsnightly.com/stats",
 "newstat_players":"https://newstat.app/"
}
common={"Season":"2026-27","SeasonType":"Regular Season","MeasureType":"Advanced","PerMode":"Totals","LeagueID":"00","LastNGames":"0","Month":"0","OpponentTeamID":"0","TeamID":"0","PlusMinus":"N","PaceAdjust":"N","Rank":"N","DateFrom":"","DateTo":"","GameScope":"","GameSegment":"","Location":"","Outcome":"","Period":"0","SeasonSegment":"","ShotClockRange":"","VsConference":"","VsDivision":""}
sources["nba_stats_team_api"]="https://stats.nba.com/stats/leaguedashteamstats?"+urlencode(common)
player=dict(common);player.update({"College":"","Conference":"","Country":"","DraftPick":"","DraftYear":"","Height":"","PlayerExperience":"","PlayerPosition":"","StarterBench":"","Weight":""})
sources["nba_stats_player_api"]="https://stats.nba.com/stats/leaguedashplayerstats?"+urlencode(player)
out={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"sources":{}}
for name,url in sources.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA source verification pilot)",
    "Accept":"application/json,text/html;q=0.9,*/*;q=0.5"})
  with urllib.request.urlopen(req,timeout=13) as response:
   raw=response.read(3_000_000)
   type_=response.headers.get("Content-Type","")
  result={"httpStatus":200,"bytes":len(raw),"contentType":type_}
  if "json" in type_.lower() or raw.startswith(b'{"resource"') or raw.startswith(b'{"result'):
   try:
    data=json.loads(raw)
    result["jsonTopKeys"]=list(data)[:16] if isinstance(data,dict) else []
    sets=data.get("resultSets",data.get("resultSet",[])) if isinstance(data,dict) else []
    if isinstance(sets,dict):sets=[sets]
    result["sets"]=[{"headers":x.get("headers",[])[:35],"rowCount":len(x.get("rowSet",[])),"example":str(x.get("rowSet",[[]])[0][:5])[:100] if x.get("rowSet") else ""} for x in sets[:3]]
   except Exception as e:result["parseError"]=str(e)[:100]
  else:
   decoded=raw.decode("utf-8","replace")
   tables=Tables();tables.feed(decoded)
   result["tables"]=[{"rows":len(t),"header":t[0][:24] if t else [],"example":t[1][:6] if len(t)>1 else []} for t in tables.tables[:5]]
   result["maxRows"]=max([len(t) for t in tables.tables],default=0)
   result["advancedTokens"]={k:len(re.findall(k,decoded,re.I)) for k in ["OFF_RATING","DEF_RATING","NET_RATING","OffRtg","NetRtg"]}
   result["isNextData"]="__NEXT_DATA__" in decoded
  out["sources"][name]=result
 except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,TimeoutError) as e:
  out["sources"][name]={"status":"unavailable","reason":f"{type(e).__name__}: {str(e)[:140]}"}
 print(name,out["sources"][name].get("httpStatus",out["sources"][name].get("status")),flush=True)
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/ratings_source_probe.json").write_text(json.dumps(out,indent=2)+"\n")
