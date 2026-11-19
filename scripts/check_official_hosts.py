#!/usr/bin/env python3
"""Read-only reachability audit of known first-party NBA source endpoints.

No proxies, cookies, rotation, scraping bypasses or external paid services.
Captures only HTTP status/content-type, never claims that 200 proves validated data.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URLS = {
  "nba_team_page": "https://www.nba.com/team/1610612752/knicks",
  "nba_player_page": "https://www.nba.com/player/1628973/jalen-brunson",
  "nba_stats_page": "https://www.nba.com/stats/teams/traditional",
  "nba_live_scoreboard_cdn": "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
  "nba_live_scoreboard_nba_s3": "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json",
  "nba_live_boxscore_nba_s3": "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/boxscore/boxscore_0022600236.json",
  "nba_schedule_cdn": "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
  "nba_official_injury_page": "https://official.nba.com/nba-injury-report-2026-27-season/",
  "nba_game_notes": "https://www.nba.com/gamenotes/knicks.pdf",
  "nba_legacy_data_domain": "https://data.nba.com/data/v2015/json/mobile_teams/nba/2026/teams/1610612752_config.json",
}
def main():
  details = {}
  for key, url in URLS.items():
    req=urllib.request.Request(url, headers={
      "User-Agent":"SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)",
      "Accept":"application/json,text/html,application/pdf;q=0.9,*/*;q=0.5"})
    try:
      with urllib.request.urlopen(req, timeout=12) as r:
        sample=r.read(512)
        details[key] = {"httpStatus":r.status, "contentType":r.headers.get("Content-Type"),
                        "nonempty":bool(sample), "url":url}
    except urllib.error.HTTPError as e:
      details[key] = {"httpStatus":e.code, "url":url, "note":"HTTP request rejected"}
    except Exception as e:
      details[key] = {"status":"unreachable","error":type(e).__name__,"url":url}
    print(key, details[key].get("httpStatus",details[key].get("status")))
  out={"checkedAtUtc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
       "checks":details,"interpretation":"A 200 means reachable, not necessarily usable or validated NBA statistics."}
  Path("data").mkdir(exist_ok=True)
  Path("data/host_checks.json").write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__":
  main()
