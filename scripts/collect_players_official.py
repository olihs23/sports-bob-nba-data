#!/usr/bin/env python3
"""Official NBA.com player profile collector, six identity-verified pilots.
Only publishes NBA.com displayed latest-5 game rows. No extrapolated season log.
"""
from __future__ import annotations
import argparse
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.error import HTTPError,URLError
from refresh_official_nba import VisibleHTML,fetch_page

# IDs and names manually verified on the OFFICIAL NBA.com player pages.
# These are an initial small batch, not a comprehensive league roster.
PLAYERS=[
 ("1628973","Jalen Brunson","NYK"),
 ("1628384","OG Anunoby","NYK"),
 ("1626157","Karl-Anthony Towns","NYK"),
 ("1628404","Josh Hart","NYK"),
 ("1628969","Mikal Bridges","NYK"),
 ("1628369","Jayson Tatum","BOS")
]
NEED=("Game Date","Matchup","MIN","PTS","FGM","FGA","3PM","3PA","FTM","FTA","REB","AST")

def read_json(path,fallback):
 try:return json.loads(path.read_text("utf-8"))
 except (OSError,ValueError):return fallback

def parse_one(page,person_id,name,team,now):
 if name not in page.text:raise ValueError("Official player identity mismatch")
 chosen=None
 for rows in page.tables:
  if not rows:continue
  head=[" ".join(h.split()) for h in rows[0]]
  if all(k in head for k in NEED):
   chosen=rows
   break
 if chosen is None:raise ValueError("Official latest games table not found")
 headers=[" ".join(h.split()) for h in chosen[0]]
 rows=[]
 for row in chosen[1:]:
  if len(row)!=len(headers):continue
  r=dict(zip(headers,row))
  try:
   dt=datetime.strptime(r["Game Date"],"%b %d, %Y")
   fields={k:int(round(float(r[k]))) for k in ("MIN","PTS","FGM","FGA","3PM","3PA","FTM","FTA","REB","AST")}
  except (KeyError,ValueError):continue
  if any(v<0 for v in fields.values()):continue
  if fields["PTS"]!=2*fields["FGM"]+fields["3PM"]+fields["FTM"] or fields["FGA"]<fields["3PA"] or fields["FGM"]<fields["3PM"] or fields["FTA"]<fields["FTM"]:
   raise ValueError("NBA box-score internal scoring mismatch")
  rows.append({"date":dt.strftime("%Y-%m-%d"),"matchup":r["Matchup"],
      "minutesRounded":fields["MIN"],**{k:v for k,v in fields.items() if k!="MIN"}})
 if not 1<=len(rows)<=5:raise ValueError(f"Got {len(rows)} valid latest-game rows")
 if len({x["date"] for x in rows})!=len(rows):raise ValueError("Duplicate game dates")
 if rows!=sorted(rows,key=lambda r:r["date"],reverse=True):raise ValueError("Unsorted game dates")
 # Published season profile averages are official values; never recompute these from 5 games.
 season={}
 for name_key in ("PPG","RPG","APG"):
  pos=[i for i,t in enumerate(page.text) if t==name_key]
  values=[]
  for i in pos:
   if i+1<len(page.text):
    try:v=float(page.text[i+1])
    except ValueError:continue
    if v>=0 and v<100: values.append(v)
  values=list(dict.fromkeys(values))
  if len(values)==1:season[name_key]=values[0]
 return {"playerId":person_id,"name":name,"teamAbbreviation":team,
  "season":"2026-27","scope":"NBA.com latest five displayed games only",
  "games":rows,"seasonAveragesOfficial":season,
  "source":f"https://www.nba.com/player/{person_id}",
  "verifiedAtUtc":now,"sourceType":"NBA.com official player page"}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--limit",type=int,default=2)
 args=p.parse_args()
 if args.limit<1 or args.limit>len(PLAYERS):raise ValueError("limit 1..6")
 path=Path("data/league/players.json")
 prior=read_json(path,{"schema":1,"season":"2026-27","items":{}})
 now=datetime.now(timezone.utc).isoformat(timespec="seconds")
 status={"schema":1,"checkedAtUtc":now,"sources":{}}
 for pid,name,team in PLAYERS[:args.limit]:
  url=f"https://www.nba.com/player/{pid}"
  try:
   entry=parse_one(fetch_page(url),pid,name,team,now)
   prior["items"][pid]=entry
   status["sources"][pid]={"name":name,"status":"verified","rows":len(entry["games"])}
  except (HTTPError,URLError,OSError,ValueError,TimeoutError) as e:
   status["sources"][pid]={"name":name,"status":"unavailable","reason":f"{type(e).__name__}: {str(e)[:150]}"}
  time.sleep(.65)
 folder=Path("data/league");folder.mkdir(parents=True,exist_ok=True)
 (folder/"players_status.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
 if prior["items"]:path.write_text(json.dumps(prior,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"verifiedPlayers":sum(x["status"]=="verified" for x in status["sources"].values()),"totalStored":len(prior["items"]),"status":status},indent=2))
if __name__=="__main__":main()
