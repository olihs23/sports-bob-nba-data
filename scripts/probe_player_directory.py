#!/usr/bin/env python3
"""Diagnostic only; never published as official player identity data."""
import json, re
from datetime import datetime,timezone
from pathlib import Path
from collect_league_official import LinkParser, fetch_html
from refresh_official_nba import VisibleHTML
url="https://www.nba.com/players"
out={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),"url":url}
try:
 html=fetch_html(url)
 a=LinkParser();a.feed(html)
 p=VisibleHTML();p.feed(html)
 out["totalLinks"]=len(a.records)
 out["linkSamples"]=a.records[:6]
 out["tables"]=[{"rows":len(t),"columns":t[0][:10],"examples":t[1:3]} for t in p.tables[:3] if t]
 out["idPatternCounts"]={
   "personId":len(re.findall(r'"personId"\s*:\s*"?\d+',html)),
   "playerId":len(re.findall(r'"playerId"\s*:\s*"?\d+',html)),
   "slashPlayer":len(re.findall(r'/player/\d{7,10}',html))
 }
except Exception as exc:out["error"]=f"{type(exc).__name__}: {str(exc)[:200]}"
Path("data/league").mkdir(exist_ok=True,parents=True)
Path("data/league/player_directory_probe.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
