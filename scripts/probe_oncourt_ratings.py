#!/usr/bin/env python3
"""Check complete unqualified team/player on-court ratings availability via free sources.
Read-only. No data promoted to verified without per-row identity and source checks.
"""
import json,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
class Tables(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.tables=[];self.table=None;self.row=None;self.cell=None;self.anchor=None
 def handle_starttag(self,t,attrs):
  if t=="table":self.table=[]
  elif t=="tr" and self.table is not None:self.row=[]
  elif t in ("td","th") and self.row is not None:self.cell=[]
  elif t=="a" and self.cell is not None:self.anchor=dict(attrs).get("href")
 def handle_data(self,t):
  if self.cell is not None:self.cell.append(t.strip())
 def handle_endtag(self,t):
  if t in ("td","th") and self.row is not None and self.cell is not None:
   self.row.append(" ".join(x for x in self.cell if x));self.cell=None
  elif t=="tr" and self.table is not None and self.row is not None:
   if self.row:self.table.append(self.row)
   self.row=None
  elif t=="table" and self.table is not None:
   self.tables.append(self.table);self.table=None
urls={
"junkie_teams":"https://hoopsjunkie.io/stats/2026-27/teams/advanced/offensive-rating",
"junkie_players_qualified":"https://hoopsjunkie.io/stats/2026-27/players/advanced/offensive-rating",
"junkie_players_relaxed_1":"https://hoopsjunkie.io/stats/2026-27/players/advanced/offensive-rating?qualifiers=relaxed",
"junkie_players_relaxed_2":"https://hoopsjunkie.io/stats/2026-27/players/advanced/offensive-rating?qualifiers=relaxed&page=2",
"junkie_players_relaxed_6":"https://hoopsjunkie.io/stats/2026-27/players/advanced/offensive-rating?qualifiers=relaxed&page=6",
"junkie_players_relaxed_10":"https://hoopsjunkie.io/stats/2026-27/players/advanced/offensive-rating?qualifiers=relaxed&page=10",
"junkie_players_def_relaxed":"https://hoopsjunkie.io/stats/2026-27/players/advanced/defensive-rating?qualifiers=relaxed",
"junkie_players_net_relaxed":"https://hoopsjunkie.io/stats/2026-27/players/advanced/net-rating?qualifiers=relaxed",
"hoopsnightly_team":"https://hoopsnightly.com/stats",
"basketball_reference_player":"https://www.basketball-reference.com/leagues/NBA_2027_advanced.html"
}
out={"atUtc":datetime.now(timezone.utc).isoformat(),"data":{}}
for name,url in urls.items():
 try:
  r=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA research verification pilot)","Accept":"text/html"})
  with urllib.request.urlopen(r,timeout=16) as response:raw=response.read(2_500_000)
  t=Tables();t.feed(raw.decode("utf-8","replace"))
  tables=[{"length":len(v),"topRows":v[:3],"lastRow":v[-1:] if v else []} for v in t.tables]
  out["data"][name]={"status":"reachable","bytes":len(raw),"tables":sorted(tables,key=lambda x:x["length"],reverse=True)[:2]}
 except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError) as e:
  out["data"][name]={"status":"unavailable","error":str(e)[:110]}
 print(name,out["data"][name]["status"],flush=True)
Path("data/league").mkdir(exist_ok=True,parents=True)
Path("data/league/oncourt_ratings_probe.json").write_text(json.dumps(out,indent=2)+"\n")
