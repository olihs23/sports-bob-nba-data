#!/usr/bin/env python3
"""Audit ALL persisted official 2026-27 game and player records; no estimates."""
import json
from pathlib import Path
from datetime import datetime,timezone
root=Path("data/season")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
index=read(root/"index.json")
players=read(root/"players.json")
manifest=read(root/"manifest.json")
game_ids={g["gameId"] for g in index["games"]}
fail=[]
if len(game_ids)!=len(index["games"]):fail.append("Duplicate indexed games")
observed={}
for pid,p in players["players"].items():
 if p["playerId"]!=pid:fail.append("Person ID mismatch "+pid)
 for row in p["games"]:
  key=(row["gameId"],pid)
  if key in observed:fail.append("Duplicate player-game "+str(key))
  observed[key]=row
  if row["gameId"] not in game_ids:fail.append("Player has unindexed game "+str(key))
  s=row["stats"]
  needed=["PTS","REB","AST","3PM","3PA","FGM","FGA","FTM","FTA","FG%","3P%","FT%","+/-","OREB","DREB","STL","BLK","TOV","PF","2PM","2PA"]
  if any(k not in s or not isinstance(s[k],(int,float)) for k in needed):fail.append("Missing full stats "+str(key))
  if s["PTS"]!=2*s["FGM"]+s["3PM"]+s["FTM"]:fail.append("PTS reconcile "+str(key))
  if s["FGA"]-s["3PA"]!=s["2PA"] or s["FGM"]-s["3PM"]!=s["2PM"]:fail.append("Two point reconcile "+str(key))
  if not (isinstance(row["minutes"],str) and row["minutes"].startswith("PT")):fail.append("Minutes invalid "+str(key))
games_valid=0
for item in index["games"]:
 path=root/"games"/(item["gameId"]+".json")
 if not path.is_file():fail.append("No original game file "+item["gameId"]);continue
 g=read(path);games_valid+=1
 if g["gameId"]!=item["gameId"] or g["status"]!="Final":fail.append("Original final-game mismatch "+item["gameId"])
 for side in ("away","home"):
  a=g[side]
  if a["team"]!=item[side]["team"] or a["score"]!=item[side]["score"]:fail.append("Team/score mismatch "+item["gameId"]+side)
  if not a["players"]:fail.append("No participating player rows "+item["gameId"]+side)
  for p in a["players"]:
   k=(item["gameId"],p["playerId"]);stored=observed.get(k)
   if not stored:fail.append("Missing player row "+str(k));continue
   if stored["stats"]!=p["stats"] or stored["minutes"]!=p["minutes"] or stored["team"]!=a["team"]:fail.append("Player fields differ "+str(k))
result={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
 "source":"NBA first-party stored boxscore records",
 "season":"2026-27","indexedFinalGames":len(index["games"]),
 "originalGameFilesVerified":games_valid,
 "uniquePlayers":len(players["players"]),
 "playerGameRows":len(observed),
 "manifestUnresolvedGameSources":len(manifest["failedGameIds"]),
 "unresolved":manifest["failedGameIds"],
 "completeAmongStoredFinalGames":len(fail)==0,
 "problems":fail[:100],
 "note":"This checks all SAVED games, not a guarantee that NBA.com has no newer finals or that originally blocked sources have since become available. Advanced ratings are not computed."}
(root/"integrity_audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
if fail:raise SystemExit("FAILED: source audit found discrepancies")
