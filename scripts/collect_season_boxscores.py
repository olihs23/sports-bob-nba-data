#!/usr/bin/env python3
"""Build actual 2026-27 NBA season game/player history from first-party NBA pages.

Authoritative index: dated https://www.nba.com/games?date=YYYY-MM-DD pages.
Authoritative box score: NBA-operated mediaops S3 /NBA/liveData/boxscore/.
No paid APIs, third-party scores, guessed player IDs, calculated stat/rank data,
or attempts to bypass denied requests. Save only verified finished games.

First launch pilot: --start 2026-11-15 --end 2026-11-15
Full season: --start 2026-10-20 --end <today EST>
Data is additive: failures never wipe older validated games. A coverage
manifest shows incomplete dates and missed boxscores rather than claiming all.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import re
import time
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from zoneinfo import ZoneInfo

ROOT=Path("data/season")
GAME_DIR=ROOT/"games"
YEAR="2026-27"
ET=ZoneInfo("America/New_York")
FIRST=date(2026,10,20)
LAST_ALLOWED=datetime.now(ET).date()
SOURCE="https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_"
DAILY="https://www.nba.com/games?date="
AGENT="SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)"
STAT_MAP={
  "PTS":"points","REB":"reboundsTotal","AST":"assists",
  "3PM":"threePointersMade","3PA":"threePointersAttempted",
  "FGM":"fieldGoalsMade","FGA":"fieldGoalsAttempted",
  "FTM":"freeThrowsMade","FTA":"freeThrowsAttempted",
  "OREB":"reboundsOffensive","DREB":"reboundsDefensive",
  "STL":"steals","BLK":"blocks","TOV":"turnovers","PF":"foulsPersonal"
}
# These are ACTUAL fields on the official NBA live-data player statistics row.
# FG%, 3P%, FT% and 2P% are stored in NBA decimal fraction form (0..1);
# conversion to a displayed percentage is presentation only, not a modeled stat.
EXTRA_PERCENT = {"FG%":"fieldGoalsPercentage","3P%":"threePointersPercentage",
  "FT%":"freeThrowsPercentage","2P%":"twoPointersPercentage"}
EXTRA_INT = {"2PM":"twoPointersMade","2PA":"twoPointersAttempted",
  "FBPTS":"pointsFastBreak","PIP":"pointsInThePaint",
  "2NDPTS":"pointsSecondChance","TOVPTS":"pointsFromTurnovers",
  "FOULSDRAWN":"foulsDrawn","OFOULS":"foulsOffensive",
  "TFOULS":"foulsTechnical","BLKREC":"blocksReceived"}
class NotFinal(Exception):pass

def fetch(url,max_bytes=4_000_000):
 req=Request(url,headers={"User-Agent":AGENT,
          "Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
 with urlopen(req,timeout=17) as r:
  if r.status!=200:raise ValueError(f"HTTP {r.status}")
  b=r.read(max_bytes+1)
  if len(b)>max_bytes:raise ValueError("Response exceeds size limit")
  return b

def iso_et(utc):
 return datetime.fromisoformat(utc.replace("Z","+00:00")).astimezone(ET).date()

def one_game(game_id,accepted_days):
 """Return (game id, saved record, skip note); do not save incomplete games."""
 url=SOURCE+game_id+".json"
 try:
  data=json.loads(fetch(url,1_000_000))
  game=data["game"]
  if str(game.get("gameId"))!=game_id:raise ValueError("Game ID mismatch")
  if game.get("gameStatus")!=3:raise NotFinal("Not final")
  played_day=iso_et(game["gameTimeUTC"])
  if played_day not in accepted_days:
   raise ValueError("Game date not present in corresponding official daily page")
  if not (FIRST<=played_day<=LAST_ALLOWED):raise ValueError("Outside season window")
  sides=[]
  ids=set()
  for key in ("awayTeam","homeTeam"):
   team=game[key]
   team_id=str(team["teamId"])
   if team_id in ids or not (team_id.isdigit() and int(team_id)>0):
    raise ValueError("Invalid or duplicated team ID")
   ids.add(team_id)
   players=[]
   for p in team.get("players",[]):
    if str(p.get("played"))!="1":continue
    stats=p.get("statistics",{})
    row={}
    for k,official_key in STAT_MAP.items():
     value=stats.get(official_key)
     if not isinstance(value,(int,float)) or isinstance(value,bool) or int(value)!=value or value<0:
      raise ValueError(f"Invalid {k} field for player {p.get('name')}")
     row[k]=int(value)
    for k,official_key in EXTRA_PERCENT.items():
     v=stats.get(official_key)
     if not isinstance(v,(int,float)) or isinstance(v,bool) or not 0<=v<=1:
      raise ValueError(f"Missing/invalid official {k} for {p.get('name')}")
     row[k]=float(v)
    for k,official_key in EXTRA_INT.items():
     v=stats.get(official_key)
     if not isinstance(v,(int,float)) or isinstance(v,bool) or int(v)!=v or v<0:
      raise ValueError(f"Missing/invalid official {k} for {p.get('name')}")
     row[k]=int(v)
    pm=stats.get("plusMinusPoints")
    if not isinstance(pm,(int,float)) or isinstance(pm,bool) or int(pm)!=pm or abs(pm)>200:
     raise ValueError(f"Missing/invalid official plus-minus for {p.get('name')}")
    row["+/-"]=int(pm)
    if row["PTS"] != 2*row["FGM"]+row["3PM"]+row["FTM"]:
     raise ValueError("Player points don't reconcile")
    if row["FGA"]<row["FGM"] or row["3PA"]<row["3PM"] or row["FTA"]<row["FTM"]:
     raise ValueError("Attempts below makes")
    if row["2PA"]!=row["FGA"]-row["3PA"] or row["2PM"]!=row["FGM"]-row["3PM"]:
     raise ValueError("Official 2PT stats do not reconcile to FG and 3PT totals")
    pid=str(p["personId"])
    if not pid.isdigit() or not str(p.get("name","")).strip():raise ValueError("Player identity missing")
    players.append({"playerId":pid,"name":p["name"],"teamId":team_id,
        "team":team.get("teamTricode"),"starter":str(p.get("starter"))=="1",
        "minutes":stats.get("minutes",""),"stats":row})
   if not players:raise ValueError("Missing participating players")
   sides.append({"teamId":team_id,"team":team["teamTricode"],
       "name":team.get("teamCity","")+" "+team.get("teamName",""),
       "score":team["score"],"players":players})
  return game_id,{"gameId":game_id,"date":str(played_day),
        "gameTimeUTC":game["gameTimeUTC"],"status":"Final",
        "season":YEAR,"source":url,"away":sides[0],"home":sides[1]},None
 except NotFinal as e:
  return game_id,None,"not_final"
 except (ValueError,KeyError,TypeError,OSError,URLError,HTTPError,json.JSONDecodeError) as e:
  return game_id,None,f"{type(e).__name__}: {str(e)[:120]}"

def load_json(path,fallback):
 try:return json.loads(path.read_text(encoding="utf-8"))
 except (OSError,ValueError):return fallback

def put_json(path,content):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(".tmp")
 temp.write_text(json.dumps(content,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 temp.replace(path)

def main():
 cli=argparse.ArgumentParser()
 cli.add_argument("--start",default="2026-10-20")
 cli.add_argument("--end",default=LAST_ALLOWED.isoformat())
 cli.add_argument("--max-new",type=int,default=350)
 cli.add_argument("--workers",type=int,default=4)
 args=cli.parse_args()
 start=date.fromisoformat(args.start);end=date.fromisoformat(args.end)
 if start<FIRST or end<start or end>LAST_ALLOWED:
  raise ValueError("Invalid current-season dates")
 if not 1<=args.max_new<=500 or not 1<=args.workers<=6:
  raise ValueError("Invalid resource limits")
 ROOT.mkdir(parents=True,exist_ok=True);GAME_DIR.mkdir(parents=True,exist_ok=True)
 now=datetime.now(timezone.utc).isoformat(timespec="seconds")
 days=[start+timedelta(days=i) for i in range((end-start).days+1)]
 pages={};candidate_days={};errors={}
 for day in days:
  key=str(day)
  try:
   html=fetch(DAILY+key,900_000).decode("utf-8","replace")
   # Additional site-wide game links can occur on every page. An individual
   # game is saved only if its boxscore date occurs among the indexed dates.
   ids=set(re.findall(r"002260\d{4}",html))
   if not ids:raise ValueError("No season game IDs in official daily page")
   pages[key]={"status":"retrieved","candidateIds":len(ids)}
   for game_id in ids:candidate_days.setdefault(game_id,set()).add(day)
  except (HTTPError,URLError,OSError,ValueError) as e:
   pages[key]={"status":"unavailable","reason":f"{type(e).__name__}: {str(e)[:90]}"}
  time.sleep(.10)
 print("Indexed dates",len(days),"with readable pages",sum(v["status"]=="retrieved" for v in pages.values()),"unique ids",len(candidate_days),flush=True)
 pending=[]
 for gid,dated in sorted(candidate_days.items()):
  existing=load_json(GAME_DIR/(gid+".json"),None)
  if existing and existing.get("gameId")==gid and existing.get("status")=="Final":
   # Backfill the official shooting percentages and +/- into previously saved
   # 2026-27 finals, without dropping a verified record if an NBA request fails.
   participants=existing.get("away",{}).get("players",[])+existing.get("home",{}).get("players",[])
   if participants and all(isinstance(x.get("stats",{}).get("FG%"),(int,float))
       and isinstance(x.get("stats",{}).get("+/-"),int) for x in participants):
    continue
  pending.append((gid,dated))
 if len(pending)>args.max_new:pending=pending[:args.max_new]
 new_count=0;not_final=[];failed={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
  futures={executor.submit(one_game,gid,dayset):gid for gid,dayset in pending}
  for f in concurrent.futures.as_completed(futures):
   gid,row,issue=f.result()
   if row:
    put_json(GAME_DIR/(gid+".json"),row);new_count+=1
   elif issue=="not_final":not_final.append(gid)
   else:failed[gid]=issue
   if (new_count+len(failed)+len(not_final))%30==0:print("Checked",new_count+len(failed)+len(not_final),"new games",new_count,flush=True)
 # Summaries created from ONLY saved first-party completed boxscore rows.
 records=[]
 for path in GAME_DIR.glob("00226*.json"):
  row=load_json(path,None)
  if row and row.get("status")=="Final" and row.get("season")==YEAR:
   if FIRST<=date.fromisoformat(row["date"])<=end:
    records.append(row)
 records.sort(key=lambda g:(g["date"],g["gameId"]))
 players={}
 summary=[]
 for g in records:
  summary.append({"gameId":g["gameId"],"date":g["date"],"timeUTC":g["gameTimeUTC"],
    "away":{k:g["away"][k] for k in ("teamId","team","score")},
    "home":{k:g["home"][k] for k in ("teamId","team","score")},
    "source":g["source"]})
  for side in ("away","home"):
   for p in g[side]["players"]:
    pid=p["playerId"]
    ent=players.setdefault(pid,{"playerId":pid,"name":p["name"],"games":[]})
    ent["name"]=p["name"]
    ent["games"].append({"gameId":g["gameId"],"date":g["date"],
      "teamId":p["teamId"],"team":p["team"],"opponent":g["home" if side=="away" else "away"]["team"],
      "home":side=="home","starter":p["starter"],"minutes":p["minutes"],
      "stats":p["stats"],"source":g["source"]})
 for p in players.values():p["games"].sort(key=lambda v:(v["date"],v["gameId"]),reverse=True)
 put_json(ROOT/"index.json",{"schema":1,"season":YEAR,"scope":"verified final regular season NBA boxscores",
    "sourceIndex":DAILY,"generatedAtUtc":now,"games":summary})
 put_json(ROOT/"players.json",{"schema":1,"season":YEAR,"scope":"observed player appearances from verified NBA final boxscores",
    "generatedAtUtc":now,"players":players})
 manifest={"schema":1,"season":YEAR,"checkedAtUtc":now,
  "searchedDates":{"start":str(start),"end":str(end),"count":len(days)},
  "officialDayPages":pages,"candidateGameIds":len(candidate_days),
  "completedGamesStored":len(records),"participatingPlayers":len(players),
  "playerAppearances":sum(len(p["games"]) for p in players.values()),
  "newGamesStored":new_count,"notFinalGameIds":sorted(not_final),
  "failedGameIds":failed,"allDatePagesRetrieved":all(v["status"]=="retrieved" for v in pages.values()),
  "scopeWarning":"Only final NBA 2026-27 regular-season games recovered from official dated NBA.com game pages and verified official NBA game boxscores. A source failure or incomplete page makes coverage incomplete. No calculated ratings, season stats, or ranks."}
 put_json(ROOT/"manifest.json",manifest)
 print(json.dumps({"new":new_count,"total":len(records),"players":len(players),
  "appearances":manifest["playerAppearances"],"dates":len(days),
  "datePagesOK":manifest["allDatePagesRetrieved"],"failed":len(failed),"notFinal":len(not_final)},indent=2),flush=True)

if __name__=="__main__":main()
