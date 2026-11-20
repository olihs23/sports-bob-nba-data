#!/usr/bin/env python3
"""Collect 30 published 2026-27 team ratings, verbatim from licensed provider CSV.

All 30 teams mandatory, all numeric rating fields must be valid. Does NOT
generate or estimate the ratings itself. Source describes these as estimates.
CC BY 4.0; attribution and license links retained with data.
"""
import csv,io,json,math
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from pathlib import Path
URL="https://boxscorelab.com/downloads/2026-27-team-standings.csv"
TEAM_CODES="""ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS""".split()
REQUIRED=("season","team","team_name","wins","losses","games","off_rating_est","def_rating_est","net_rating","pace")
def main():
 request=Request(URL,headers={"User-Agent":"SportsBobResearch/0.1 (+CC BY 4.0 CSV research client)","Accept":"text/csv,text/plain;q=0.9,*/*;q=0.2"})
 with urlopen(request,timeout=24) as response:
  if response.status!=200:raise ValueError("Provider status is not 200")
  raw=response.read(100_001)
 if len(raw)>100_000:raise ValueError("Unexpected CSV size")
 reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
 if not all(k in (reader.fieldnames or []) for k in REQUIRED):
  raise ValueError("Provider schema changed")
 rows=list(reader)
 if len(rows)!=30:raise ValueError(f"Expected 30 team rows, received {len(rows)}")
 items={}
 for r in rows:
  abbr=r["team"]
  if r["season"]!="2026-27" or abbr not in TEAM_CODES or abbr in items:
   raise ValueError("Invalid season, team ID or duplicate")
  if not str(r["team_name"]).strip():raise ValueError("Missing team identity")
  fields={}
  for key,source in (("offRating","off_rating_est"),("defRating","def_rating_est"),("netRating","net_rating"),("pace","pace")):
   try:v=float(r[source])
   except (ValueError,TypeError):raise ValueError(f"{abbr}: missing {source}")
   if not math.isfinite(v):raise ValueError(f"{abbr}: non-finite {source}")
   if key in ("offRating","defRating") and not 60<=v<=180:raise ValueError("Out-of-range rating")
   if key=="netRating" and not -80<=v<=80:raise ValueError("Out-of-range net")
   if key=="pace" and not 65<=v<=135:raise ValueError("Out-of-range pace")
   fields[key]=v
  if abs(fields["offRating"]-fields["defRating"]-fields["netRating"])>0.12:
   raise ValueError(f"{abbr}: mismatched published rating columns")
  items[abbr]={"team":r["team_name"],"abbreviation":abbr,**fields,
    "sourceOriginalColumns":{"offRating":"off_rating_est","defRating":"def_rating_est","netRating":"net_rating","pace":"pace"}}
 if set(items)!=set(TEAM_CODES):raise ValueError("Provider coverage missing NBA teams")
 result={"schema":1,"season":"2026-27","provider":"BoxScore Lab",
   "source":URL,"license":"CC BY 4.0",
   "licenseUrl":"https://boxscorelab.com/downloads/",
   "methodology":"https://boxscorelab.com/methodology/",
   "verifiedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
   "ratingDefinition":"Provider's published season team OFF/DEF estimates and net rating (per 100 estimated possessions), not official NBA.com advanced values.",
   "teams":items}
 path=Path("data/league/team_advanced_estimates.json")
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"teams":len(items),"provider":result["provider"],"sample":items["NYK"]},indent=2))
if __name__=="__main__":main()
