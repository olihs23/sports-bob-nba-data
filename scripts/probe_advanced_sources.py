#!/usr/bin/env python3
"""Read-only official NBA advanced stats availability test, no synthetic ratings."""
import json,urllib.request,urllib.error,re
from pathlib import Path
from html.parser import HTMLParser
class T(HTMLParser):
 def __init__(self):
  super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.skip=False
 def handle_starttag(self,t,attrs):
  if t=="table":self.table=[]
  elif t=="tr" and self.table is not None:self.row=[]
  elif t in ("th","td") and self.row is not None:self.cell=[]
 def handle_data(self,s):
  if self.cell is not None:self.cell.append(s.strip())
 def handle_endtag(self,t):
  if t in ("th","td") and self.cell is not None and self.row is not None:
   self.row.append(" ".join(x for x in self.cell if x));self.cell=None
  elif t=="tr" and self.row is not None and self.table is not None:self.table.append(self.row);self.row=None
  elif t=="table" and self.table is not None:self.tables.append(self.table);self.table=None
u={
 "team_advanced":"https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season",
 "player_advanced":"https://www.nba.com/stats/players/advanced?Season=2026-27&SeasonType=Regular%20Season",
 "team_advanced_leaders":"https://www.nba.com/stats/teams/advanced-leaders",
 "player_advanced_leaders":"https://www.nba.com/stats/players/advanced-leaders"
}
out={}
for key,url in u.items():
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)","Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
  with urllib.request.urlopen(req,timeout=16) as resp:s=resp.read(3_000_000).decode("utf-8","replace")
  p=T();p.feed(s)
  out[key]={"http":200,"bytes":len(s),"tables":[{"rows":len(x),"columns":x[0][:24] if x else [],"sample":x[1][:20] if len(x)>1 else []} for x in p.tables[:6]],"ratingTokens":len(re.findall(r'NET_RATING|OFF_RATING|DEF_RATING',s)),"hasTableWithAll30Teams":any(len(x)>=31 for x in p.tables)}
 except (urllib.error.HTTPError,urllib.error.URLError,ValueError,OSError) as e:out[key]={"error":str(e)[:160]}
 print(key,out[key].get("http",out[key].get("error")),flush=True)
Path("data/league/advanced_source_probe.json").write_text(json.dumps(out,indent=2)+"\n")
