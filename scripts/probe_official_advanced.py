#!/usr/bin/env python3
"""One-player probe of NBA.com's own advanced ratings. No unofficial data or estimates."""
from __future__ import annotations
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PLAYER_ID = 1628973
PLAYER_NAME = "Jalen Brunson"
SEASON = "2026-27"
OUT = Path("data/diagnostics/official_advanced_brunson.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/stats/",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}
BASE = {
    "LeagueID": "00",
    "Season": SEASON,
    "SeasonType": "Regular Season",
    "MeasureType": "Advanced",
    "PerMode": "Totals",
    "LastNGames": "0",
    "Month": "0",
    "OpponentTeamID": "0",
    "Period": "0",
    "PaceAdjust": "N",
    "PlusMinus": "N",
    "Rank": "N",
    "DateFrom": "",
    "DateTo": "",
    "GameSegment": "",
    "Location": "",
    "Outcome": "",
    "SeasonSegment": "",
    "VsConference": "",
    "VsDivision": "",
}

def download(url: str, timeout: int = 8):
    started = time.monotonic()
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as response:
        raw = response.read(3_000_001)
        status = response.status
        content_type = response.headers.get("Content-Type", "")
    if len(raw) > 3_000_000:
        raise ValueError("response over 3MB limit")
    if status != 200:
        raise ValueError("HTTP status %s" % status)
    return raw, content_type, round(time.monotonic() - started, 2)

def sets_from_payload(obj):
    sets = obj.get("resultSets", obj.get("resultSet", []))
    if isinstance(sets, dict):
        sets = [sets]
    if not isinstance(sets, list):
        raise ValueError("NBA response did not contain result sets")
    return sets

def extract_ratings(raw: bytes, route: str):
    obj = json.loads(raw)
    for group in sets_from_payload(obj):
        headers = group.get("headers", [])
        if not isinstance(headers, list):
            continue
        ix = {str(k).upper(): i for i, k in enumerate(headers)}
        # Only the NBA's actual OFF/DEF/NET fields qualify.
        required = ("OFF_RATING", "DEF_RATING", "NET_RATING")
        if any(key not in ix for key in required):
            continue
        for row in group.get("rowSet", []):
            if not isinstance(row, list) or len(row) < len(headers):
                continue
            if "PLAYER_ID" in ix and str(row[ix["PLAYER_ID"]]) != str(PLAYER_ID):
                continue
            if "SEASON_YEAR" in ix and str(row[ix["SEASON_YEAR"]]) != SEASON:
                continue
            if "GROUP_VALUE" in ix and route == "year_over_year" and str(row[ix["GROUP_VALUE"]]) != SEASON:
                continue
            # For player-scoped endpoints, require a known overall/season group.
            if route == "player_dashboard" and str(group.get("name", "")).lower() not in (
                "overallplayerdashboard", "overallplayerdashboardv2"
            ):
                continue
            values = []
            for key in required:
                v = row[ix[key]]
                if isinstance(v, bool) or not isinstance(v, (float, int)):
                    break
                if not math.isfinite(v):
                    break
                values.append(float(v))
            if len(values) != 3:
                continue
            off, deff, net = values
            if not (0 < off < 250 and 0 < deff < 250 and -200 < net < 200):
                continue
            if abs((off - deff) - net) > 1.5:
                continue
            return {
                "offRating": off,
                "defRating": deff,
                "netRating": net,
                "nbaResultSet": group.get("name"),
                "playerId": PLAYER_ID,
                "season": SEASON,
                "seasonType": "Regular Season",
                "sourceType": "NBA.com official advanced statistics",
            }
    raise ValueError("no matching player-season row with all three official NBA rating fields")

def try_api(route: str, endpoint: str, params: dict):
    url = "https://stats.nba.com/stats/%s?%s" % (endpoint, urlencode(params))
    entry = {"method": route, "url": url, "status": "failed"}
    try:
        raw, content_type, elapsed = download(url)
        entry["responseSeconds"] = elapsed
        entry["contentType"] = content_type
        ratings = extract_ratings(raw, route)
        entry["status"] = "verified"
        entry["ratings"] = ratings
    except Exception as e:
        entry["error"] = "%s: %s" % (type(e).__name__, str(e)[:180])
    return entry

def try_page(route: str, url: str):
    entry = {"method": route, "url": url, "status": "failed"}
    try:
        raw, content_type, elapsed = download(url, timeout=8)
        text = raw.decode("utf-8", "replace")
        entry["responseSeconds"] = elapsed
        entry["contentType"] = content_type
        entry["status"] = "html_loaded_no_verified_ratings"
        entry["containsAdvancedText"] = "Advanced" in text
        entry["containsOffRatingToken"] = "OFF_RATING" in text or "OFFRTG" in text
        entry["note"] = "HTML alone is not accepted as proof of an official season rating."
    except Exception as e:
        entry["error"] = "%s: %s" % (type(e).__name__, str(e)[:180])
    return entry

def main():
    common = dict(BASE)
    league = dict(common, TeamID="0", TwoWay="", PlayerExperience="", PlayerPosition="",
                  College="", Conference="", Country="", Division="", DraftPick="",
                  DraftYear="", GameScope="", Height="", Weight="", ShotClockRange="",
                  StarterBench="", PORound="", GameSegment="")
    dash = dict(common, PlayerID=str(PLAYER_ID))
    year = dict(common, PlayerID=str(PLAYER_ID))
    attempts = [
        try_api("league_advanced", "leaguedashplayerstats", league),
        try_api("player_dashboard", "playerdashboardbygeneralsplits", dash),
        try_api("year_over_year", "playerdashboardbyyearoveryear", year),
        try_page("nba_player_page", "https://www.nba.com/stats/player/%s/advanced?Season=%s" % (PLAYER_ID, SEASON)),
        try_page("nba_league_page", "https://www.nba.com/stats/players/advanced?Season=%s" % SEASON),
    ]
    good = [x for x in attempts if x["status"] == "verified"]
    # Diagnostic only: no automatic insertion into player/team research records.
    report = {
        "schema": 1,
        "scope": "One-player diagnostic; do not use as a production ratings data feed",
        "playerId": PLAYER_ID,
        "playerName": PLAYER_NAME,
        "season": SEASON,
        "seasonType": "Regular Season",
        "checkedAtUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "verified_official_api" if good else "unavailable",
        "verifiedSourceCount": len(good),
        "attempts": attempts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NBA.com one-player OFFRTG / DEFRTG / NETRTG probe:", report["status"])
    for a in attempts:
        print(a["method"], a["status"], a.get("error", ""))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
