#!/usr/bin/env python3
"""Sports Bob NBA.com expansion: verified team profiles and official roster discovery.

Uses ONLY NBA.com public team profile pages, no third-party estimates.
Safeguards: every individual record has an NBA.com URL, check date, identity;
unavailable records retain the last VERIFIED copy and are flagged. No guessed ranks.
Standard-library only. On first run, pilot two teams. Opt in to all teams after audit.
"""
from __future__ import annotations
import argparse
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TEAMS={
    "ATL":(1610612737,"Atlanta Hawks"),"BOS":(1610612738,"Boston Celtics"),
    "BKN":(1610612751,"Brooklyn Nets"),"CHA":(1610612766,"Charlotte Hornets"),
    "CHI":(1610612741,"Chicago Bulls"),"CLE":(1610612739,"Cleveland Cavaliers"),
    "DAL":(1610612742,"Dallas Mavericks"),"DEN":(1610612743,"Denver Nuggets"),
    "DET":(1610612765,"Detroit Pistons"),"GSW":(1610612744,"Golden State Warriors"),
    "HOU":(1610612745,"Houston Rockets"),"IND":(1610612754,"Indiana Pacers"),
    "LAC":(1610612746,"LA Clippers"),"LAL":(1610612747,"Los Angeles Lakers"),
    "MEM":(1610612763,"Memphis Grizzlies"),"MIA":(1610612748,"Miami Heat"),
    "MIL":(1610612749,"Milwaukee Bucks"),"MIN":(1610612750,"Minnesota Timberwolves"),
    "NOP":(1610612740,"New Orleans Pelicans"),"NYK":(1610612752,"New York Knicks"),
    "OKC":(1610612760,"Oklahoma City Thunder"),"ORL":(1610612753,"Orlando Magic"),
    "PHI":(1610612755,"Philadelphia 76ers"),"PHX":(1610612756,"Phoenix Suns"),
    "POR":(1610612757,"Portland Trail Blazers"),"SAC":(1610612758,"Sacramento Kings"),
    "SAS":(1610612759,"San Antonio Spurs"),"TOR":(1610612761,"Toronto Raptors"),
    "UTA":(1610612762,"Utah Jazz"),"WAS":(1610612764,"Washington Wizards")
}
assert len(TEAMS)==30
from refresh_official_nba import VisibleHTML, fetch_page, ordinal, STAT_NAMES

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current=None
        self.records=[]
        self.depth=0
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href","")
            m=re.search(r"(?<!\w)/player/(\d{7,10})(?:/([a-z0-9-]+))?(?:[?#]|$)",href)
            self.current=(m.group(1),m.group(2),[]) if m else None
    def handle_data(self,s):
        if self.current:
            self.current[2].append(s)
    def handle_endtag(self,tag):
        if tag=="a" and self.current:
            p_id,slug,tokens=self.current
            name=" ".join(" ".join(tokens).split())
            if name and len(name)<=100:
                self.records.append((p_id,slug or "",name))
            self.current=None

def fetch_html(url):
    req=Request(url,headers={
        "User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)",
        "Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"
    })
    with urlopen(req,timeout=20) as resp:
        if resp.status!=200: raise ValueError(f"NBA returned {resp.status}")
        raw=resp.read(4_000_001)
    if len(raw)>4_000_000: raise ValueError("Page too large")
    return raw.decode("utf-8","replace")

def parse_general_team(html,abbr,now):
    team_id,full_name=TEAMS[abbr]
    visible=VisibleHTML()
    visible.feed(html)
    tokens=visible.text
    # Check official team identity before trusting numbers.
    nickname=full_name.split()[-1].lower()
    if nickname not in [s.lower() for s in tokens]:
        raise ValueError("Page identity not verified: "+full_name)
    metrics={}
    for label,key in STAT_NAMES.items():
        candidates=[]
        for i,val in enumerate(tokens):
            if val.upper()!=label: continue
            for end in range(i+2,min(i+5,len(tokens))):
                rank=ordinal(" ".join(tokens[i+1:end]))
                if rank is None: continue
                try:v=float(tokens[end].replace(",",""))
                except ValueError: continue
                lo,hi=(70,165) if label in ("PPG","OPPG") else (20,85) if label=="RPG" else (10,55)
                if lo<=v<=hi: candidates.append((v,rank))
        candidates=list(dict.fromkeys(candidates))
        if len(candidates)!=1:
            raise ValueError(f"{abbr} {label} ambiguous/missing: {len(candidates)}")
        v,rank=candidates[0]
        metrics[key]={"value":v,"nbaRank":rank}
    return {"teamId":str(team_id),"team":full_name,"abbreviation":abbr,
            "season":"2026-27","seasonType":"Regular Season","stats":metrics,
            "source":f"https://www.nba.com/team/{team_id}",
            "verifiedAtUtc":now,"sourceType":"official NBA.com team profile"}

def parse_official_roster(html,abbr,now):
    team_id,full_name=TEAMS[abbr]
    parser=LinkParser()
    parser.feed(html)
    player_map={}
    for p_id,slug,name in parser.records:
        # Player profile links can occur elsewhere on team page. A roster
        # must be backed by its own named ROSTER table rather than all links.
        player_map.setdefault(p_id,{"playerId":p_id,"name":name,
            "profile":f"https://www.nba.com/player/{p_id}"+(f"/{slug}" if slug else "")})
    visible=VisibleHTML()
    visible.feed(html)
    rows=[]
    for table in visible.tables:
        if not table: continue
        header=[c.lower() for c in table[0]]
        if "player" in header and "pos" in header:
            rows=table[1:]
            break
    if not rows or len(rows)<5 or len(rows)>30:
        raise ValueError(f"Official NBA roster table missing/unusable: {len(rows)} rows")
    players=[]
    for row in rows:
        if len(row)<3: continue
        name=row[0].strip()
        # Many player profile links use text exactly matching the official roster.
        matches=[p for p in player_map.values() if p["name"].casefold()==name.casefold()]
        if len(matches)!=1: continue
        item=dict(matches[0])
        item["position"]=row[2]
        players.append(item)
    if len(players)<5:
        raise ValueError(f"Only {len(players)} resolved; anchors={len(parser.records)} sample={parser.records[:2]} rosterNames={[r[0] for r in rows[:2]]}")
    if len({p["playerId"] for p in players})!=len(players):
        raise ValueError("Duplicate official NBA player IDs")
    return {"teamId":str(team_id),"team":full_name,"abbreviation":abbr,
            "season":"2026-27","verifiedAtUtc":now,
            "source":f"https://www.nba.com/team/{team_id}/roster",
            "players":players,"scope":"Current official team roster, not game participation"}

def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    tmp.replace(path)

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--limit",type=int,default=2,help="Max team pages for this run (1..30)")
    cli.add_argument("--offset",type=int,default=0)
    args=cli.parse_args()
    if not 1<=args.limit<=30 or not 0<=args.offset<30:raise ValueError("invalid batch")
    batch=list(TEAMS)[args.offset:args.offset+args.limit]
    now=datetime.now(timezone.utc).isoformat(timespec="seconds")
    out=Path("data/league")
    prior={}
    for kind in ("teams","rosters"):
        path=out/f"{kind}.json"
        try:prior[kind]=json.loads(path.read_text()) 
        except (OSError,ValueError):prior[kind]={"season":"2026-27","items":{}}
    status={"schema":1,"checkedAtUtc":now,"batch":batch,"sources":{}}
    for team in batch:
        url=f"https://www.nba.com/team/{TEAMS[team][0]}"
        status["sources"][team]={}
        try:
            html=fetch_html(url)
        except (HTTPError,URLError,OSError,ValueError) as e:
            status["sources"][team]["page"]={"status":"unavailable","reason":str(e)[:140]}
            continue
        for kind,parser in (("teams",parse_general_team),("rosters",parse_official_roster)):
            try:
                parsed=parser(html,team,now)
                prior[kind]["items"][team]=parsed
                status["sources"][team][kind]={"status":"verified","count":len(parsed.get("players",[]))}
            except ValueError as e:
                status["sources"][team][kind]={"status":"unavailable","reason":str(e)[:140]}
        time.sleep(.6)
    for kind in ("teams","rosters"):
        if prior[kind]["items"]:
            prior[kind]["schema"]=1
            prior[kind]["season"]="2026-27"
            atomic_json(out/f"{kind}.json",prior[kind])
    atomic_json(out/"status.json",status)
    print(json.dumps({"collected":status,"teamCoverage":len(prior["teams"]["items"]),
        "rosterCoverage":len(prior["rosters"]["items"])},indent=2))
if __name__=="__main__":main()
