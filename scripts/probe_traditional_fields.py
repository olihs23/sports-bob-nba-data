#!/usr/bin/env python3
"""Inspect official NBA full player statistics field names; read-only verification."""
import json, urllib.request, pathlib
url="https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_0022600236.json"
request=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)","Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
with urllib.request.urlopen(request,timeout=20) as resp:data=json.load(resp)
g=data["game"];p=next((p for p in g["awayTeam"]["players"]+g["homeTeam"]["players"] if str(p.get("played"))=="1"),None)
result={"gameId":g["gameId"],"playerId":p["personId"],"name":p["name"],"statistics":p["statistics"]}
path=pathlib.Path("data/league/official_player_field_probe.json");path.parent.mkdir(exist_ok=True,parents=True);path.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
