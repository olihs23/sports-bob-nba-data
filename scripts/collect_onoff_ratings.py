#!/usr/bin/env python3
"""Collect only the publisher's explicitly CC BY 4.0 licensed on/off JSON.
No website scraping, no NBA rating formula, no estimates generated in Sports Bob.
"""
import json,math,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
URL="https://hoopsnightly.com/api/open?part=on-off"
DEST=Path("data/league/onoff_ratings.json")
def main():
 req=urllib.request.Request(URL,headers={"Accept":"application/json","User-Agent":"SportsBobResearch/0.1 (+attributed CC-BY-4.0 public JSON client)"})
 with urllib.request.urlopen(req,timeout=22) as resp:
  if resp.status!=200:raise ValueError(f"HTTP {resp.status}")
  raw=resp.read(2_500_001)
 if len(raw)>2_500_000:raise ValueError("Source exceeds size limit")
 data=json.loads(raw)
 if data.get("part")!="on-off" or data.get("license")!="CC BY 4.0":raise ValueError("Expected licensed on-off feed")
 root=data.get("data",{})
 if root.get("season")!="2026-27":raise ValueError("Wrong NBA season")
 players=root.get("players",[])
 if not isinstance(players,list) or len(players)<150:raise ValueError("Insufficient source player coverage")
 items={}
 for p in players:
  pid=str(p.get("player_id",""))
  tid=str(p.get("team_id",""))
  if not pid.isdigit() or not tid.isdigit() or not str(p.get("name","")).strip():
   continue
  keys=("on_net","off_net","swing","on_min","off_min")
  if not all(isinstance(p.get(k),(int,float)) and not isinstance(p.get(k),bool) and math.isfinite(p[k]) for k in keys):continue
  if p["on_min"]<0 or p["off_min"]<0 or abs(p["on_net"])>200 or abs(p["off_net"])>200:continue
  if pid in items:raise ValueError("Duplicate NBA player ID in feed: "+pid)
  items[pid]={
   "playerId":pid,"teamId":tid,"name":p["name"],
   "teamAbbreviation":p.get("tricode"),
   "onCourtNetRating":p["on_net"],"offCourtNetRating":p["off_net"],
   "netSwing":p["swing"],"minutesOn":p["on_min"],"minutesOff":p["off_min"]
  }
 if len(items)<150:raise ValueError(f"Only {len(items)} player IDs valid")
 out={"schema":1,"season":"2026-27","provider":"Hoops Nightly",
  "source":URL,"license":"CC BY 4.0",
  "licenseUrl":"https://hoopsnightly.com/data-license",
  "ratingDefinition":"On-court net points per 100 possessions from provider's original 2026-27 on/off dataset, NOT official NBA.com advanced rating and not player individual efficiency",
  "verifiedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
  "players":items,"sourceFields":["on_net","off_net","swing","on_min","off_min"],
  "note":"No OFF RTG or DEF RTG field in licensed source. Do not calculate those or claim NBA.com source."}
 DEST.parent.mkdir(parents=True,exist_ok=True)
 DEST.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"verifiedPlayers":len(items),"season":out["season"],"source":URL,"sample":items.get("1628973")},indent=2))
if __name__=="__main__":main()
