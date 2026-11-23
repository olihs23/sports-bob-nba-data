#!/usr/bin/env python3
"""Sports Bob: free ESPN NBA daily schedule + current league injury-listing cache.
Data-only public JSON for offline HTML readers; never substitutes for official NBA medical report.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path("data/live")
BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/"
ET = ZoneInfo("America/New_York")
ALIAS = {"GS": "GSW", "NY": "NYK", "SA": "SAS", "NO": "NOP", "UTAH": "UTA", "WSH": "WAS", "PHO": "PHX", "BRK": "BKN"}
TEAMS = set("ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC ORL PHI PHX POR SAC SAS TOR UTA WAS".split())

def code(value):
    result = ALIAS.get(str(value or "").upper(), str(value or "").upper())
    return result if result in TEAMS else None

def fetch(path):
    request = Request(BASE + path, headers={"User-Agent": "SportsBobResearch/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=18) as r:
        if r.status != 200:
            raise ValueError(f"HTTP {r.status}")
        body = r.read(3_000_001)
    if len(body) > 3_000_000:
        raise ValueError("Large ESPN response rejected")
    return json.loads(body)

def save(name, obj):
    ROOT.mkdir(parents=True, exist_ok=True)
    output = ROOT / name
    output.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(name, "written", output.stat().st_size, "bytes")

def schedule(today, stamp):
    games = []
    valid_days = []
    errors = {}
    for step in range(-7, 3):
        day = today + timedelta(days=step)
        iso = day.isoformat()
        try:
            obj = fetch("scoreboard?dates=" + day.strftime("%Y%m%d"))
            leagues = obj.get("leagues", [])
            if not leagues or not any(str(x.get("abbreviation") or x.get("slug") or "").lower() == "nba" for x in leagues):
                raise ValueError("League not confirmed as NBA")
            entries = obj.get("events")
            if not isinstance(entries, list):
                raise ValueError("No event array")
            daygames = []
            seen = set()
            for event in entries:
                if event.get("season", {}).get("type") and int(event["season"]["type"]) != 2:
                    continue
                competitors = event.get("competitions", [{}])[0].get("competitors", [])
                if len(competitors) != 2:
                    raise ValueError("Missing competitors")
                who = {p.get("homeAway"): code(p.get("team", {}).get("abbreviation")) for p in competitors}
                a, h = who.get("away"), who.get("home")
                if not a or not h or a == h:
                    raise ValueError("Unrecognized NBA team")
                instant = datetime.fromisoformat(str(event["date"]).replace("Z", "+00:00")).astimezone(ET)
                if instant.date() != day:
                    raise ValueError("ESPN date differs from Eastern scheduled date")
                key = (iso, a, h)
                if key in seen:
                    raise ValueError("Duplicate team fixture")
                seen.add(key)
                st = event.get("status", {}).get("type", {})
                state = "final" if st.get("completed") else ("live" if st.get("state") == "in" else "scheduled")
                daygames.append([iso, a, h, instant.strftime("%I:%M %p").lstrip("0"), state])
            if day < today and any(g[4] != "final" for g in daygames):
                raise ValueError("Past day contains unfinalized games")
            games.extend(daygames)
            valid_days.append(iso)
        except Exception as exc:
            errors[iso] = str(exc)[:140]
    if today.isoformat() not in valid_days or len(valid_days) < 8 or len(games) < 8:
        raise ValueError("Insufficient ESPN NBA schedule coverage: " + str(errors))
    doc = {
        "schema": 1, "season": "2026-27",
        "source": "ESPN NBA scoreboard (GitHub collector)",
        "sourceUrl": BASE + "scoreboard",
        "verifiedOn": today.isoformat(), "checkedAtUtc": stamp,
        "dateRange": [(today - timedelta(days=7)).isoformat(), (today + timedelta(days=2)).isoformat()],
        "datesVerified": valid_days, "games": games, "errors": errors,
    }
    save("schedule.json", doc)

def injuries(today, stamp):
    obj = fetch("injuries")
    groups = obj if isinstance(obj, list) else (obj.get("injuries") or obj.get("teams"))
    if not isinstance(groups, list) or len(groups) < 5:
        raise ValueError("Unexpected ESPN injury schema")
    teams = {}
    total = 0
    for item in groups:
        team = code(item.get("team", {}).get("abbreviation") or item.get("abbreviation"))
        if not team:
            continue
        rows = item.get("injuries")
        if not isinstance(rows, list):
            raise ValueError("Invalid injury team schema")
        seen = set()
        result = []
        for row in rows:
            person = row.get("athlete") or {}
            name = str(person.get("displayName") or person.get("fullName") or person.get("name") or "").strip()
            if not name or len(name) > 100 or name.lower() in seen:
                continue
            seen.add(name.lower())
            status = str(row.get("status") or "").lower().replace("-", " ")
            if "out" in status:
                status = "Out"
            elif "questionable" in status:
                status = "Questionable"
            elif "doubtful" in status:
                status = "Doubtful"
            elif "probable" in status:
                status = "Probable"
            elif "available" in status or "active" in status:
                status = "Available"
            elif "day to day" in status:
                status = "Day-to-day"
            else:
                status = "Unverified"
            typ = row.get("type") or {}
            detail = row.get("details") or {}
            reason = str(typ.get("description") or detail.get("detail") or detail.get("description") or row.get("description") or "")[:180]
            result.append([name, status, reason])
        teams[team] = result
        total += len(result)
    if len(teams) < 8 or not 5 <= total <= 500:
        raise ValueError("ESPN injury listings incomplete")
    save("injuries.json", {
        "schema": 1, "season": "2026-27", "source": "ESPN NBA injury listings (GitHub collector)",
        "sourceUrl": BASE + "injuries", "checkedAtUtc": stamp,
        "checkedDate": today.isoformat(), "total": total, "coveredTeams": len(teams), "teams": teams,
        "warning": "ESPN's league-wide listings are not the NBA's official game-specific medical report."
    })

def main():
    today = datetime.now(ET).date()
    stamp = datetime.now(timezone.utc).isoformat()
    failures = []
    for name, action in (("schedule", schedule), ("injuries", injuries)):
        try:
            action(today, stamp)
        except Exception as exc:
            print(name, "NOT UPDATED", str(exc), file=sys.stderr)
            failures.append(name)
    if len(failures) == 2:
        raise SystemExit("Both ESPN feeds unavailable; older verified JSON retained")
    print("Completed. Failed categories:", failures)

if __name__ == "__main__":
    main()
