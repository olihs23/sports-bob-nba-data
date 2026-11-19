#!/usr/bin/env python3
"""Probe whether NBA.com daily games pages enumerate official game ids."""
from urllib.request import urlopen,Request
from urllib.error import URLError,HTTPError
import re,json
from pathlib import Path
urls={
 "games_nov15":"https://www.nba.com/games?date=2026-11-15",
 "games_nov19":"https://www.nba.com/games?date=2026-11-19",
 "games_oct20":"https://www.nba.com/games?date=2026-10-20",
 "schedule":"https://www.nba.com/schedule",
 "schedule_nov19":"https://www.nba.com/schedule?date=2026-11-19"
}
out={}
for k,u in urls.items():
 try:
  q=Request(u,headers={"User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)","Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
  with urlopen(q,timeout=20) as r:html=r.read(3_000_000).decode("utf-8","replace")
  ids=sorted(set(re.findall(r"002260\d{4}",html)))
  out[k]={"http":200,"bytes":len(html),"ids":ids[:30],"totalUniqueIds":len(ids),"hasSchedule":'schedule' in html.lower(),"title":re.search(r"<title[^>]*>([^<]+)",html).group(1) if re.search(r"<title[^>]*>([^<]+)",html) else None}
 except (HTTPError,URLError,OSError) as e:out[k]={"error":str(e)[:160]}
 print(k,out[k].get("totalUniqueIds",out[k].get("error")),flush=True)
Path("data/league").mkdir(parents=True,exist_ok=True)
Path("data/league/game_index_probe.json").write_text(json.dumps(out,indent=2)+"\n")
