#!/usr/bin/env python3
"""Sports Bob NBA official-source refresh PILOT — standard library only.

Fetches one NBA.com team summary (with NBA-published ranks) and one player's
latest five displayed box scores. Does NOT claim full-league/full-history
coverage, advanced stats, injury statuses, or live game availability.

NBA.com is not guaranteed to permit automated requests from GitHub's network.
Any failure is reported; previously verified data is not overwritten.
No third-party source, estimated ranking, or inferred statistic is published.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TEAM_URL = "https://www.nba.com/team/1610612752/knicks"
PLAYER_URL = "https://www.nba.com/player/1628973/jalen-brunson"
OUT = Path("data")
PROBE = {
    "team": {"abbreviation": "NYK", "name": "New York Knicks", "url": TEAM_URL},
    "player": {"id": "1628973", "name": "Jalen Brunson", "url": PLAYER_URL},
}
STAT_NAMES = {"PPG": "pointsPerGame", "OPPG": "pointsAllowedPerGame",
              "RPG": "reboundsPerGame", "APG": "assistsPerGame"}

class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text = []
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg", "noscript"):
            self.skip += 1
        if self.skip:
            return
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.skip:
            return
        val = " ".join(data.split())
        if val:
            self.text.append(val)
            if self.cell is not None:
                self.cell.append(val)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "noscript"):
            if self.skip:
                self.skip -= 1
            return
        if self.skip:
            return
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None

def fetch_page(url: str) -> VisibleHTML:
    # No proxies, no authentication and no workaround for access restrictions.
    request = Request(url, headers={
        "User-Agent": "SportsBobResearch/0.1 (+public NBA endpoint reachability pilot)",
        "Accept": "application/json,text/html,application/pdf;q=0.9,*/*;q=0.5",
    })
    with urlopen(request, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"NBA returned HTTP {resp.status}")
        raw = resp.read(4_000_001)
    if len(raw) > 4_000_000:
        raise RuntimeError("Page size exceeds safety limit")
    html = raw.decode("utf-8", "replace")
    parser = VisibleHTML()
    parser.feed(html)
    return parser

def ordinal(text: str):
    compact = re.sub(r"\s+", "", text).lower()
    match = re.fullmatch(r"(\d{1,2})(st|nd|rd|th)", compact)
    if not match:
        return None
    v = int(match.group(1))
    return v if 1 <= v <= 30 else None

def parse_team(page: VisibleHTML):
    tokens = page.text
    if not any(t.lower() == "knicks" for t in tokens):
        raise ValueError("Wrong team page")
    found = {}
    for name, key in STAT_NAMES.items():
        indices = [i for i, s in enumerate(tokens) if s.upper() == name]
        candidates = []
        for i in indices:
            for end in range(i+2, min(i+5, len(tokens))):
                rank = ordinal(" ".join(tokens[i+1:end]))
                if rank is None:
                    continue
                # The NBA summary prints a league rank immediately before its value.
                if end >= len(tokens):
                    continue
                try:
                    value = float(tokens[end].replace(",", ""))
                except ValueError:
                    continue
                low, high = ((70, 165) if name in ("PPG", "OPPG")
                             else (20, 85) if name == "RPG"
                             else (10, 55))
                if low <= value <= high:
                    candidates.append((value, rank))
        if len(candidates) != 1:
            raise ValueError(f"Couldn't unambiguously verify {name}: {len(candidates)} candidates")
        v, rank = candidates[0]
        found[key] = {"value": v, "nbaRank": rank}
    return {
        "teamId": "1610612752", "team": "New York Knicks", "abbreviation": "NYK",
        "season": "2026-27", "seasonType": "Regular Season",
        "stats": found, "source": TEAM_URL, "sourceType": "official NBA.com team profile"
    }

def parse_player(page: VisibleHTML):
    if "Jalen Brunson" not in page.text:
        raise ValueError("Wrong player page")
    expected = ["Game Date", "Matchup", "W/L", "MIN", "PTS", "FGM", "FGA"]
    table = None
    for rows in page.tables:
        if not rows:
            continue
        header = [re.sub(r"\s+", " ", s) for s in rows[0]]
        if all(x in header for x in expected):
            table = rows
            break
    if table is None:
        raise ValueError("Official player last-five game table not found")
    head = table[0]
    need = ["Game Date", "Matchup", "MIN", "PTS", "FGM", "FGA", "3PM", "3PA",
            "FTM", "FTA", "REB", "AST"]
    if not all(k in head for k in need):
        raise ValueError("Incomplete official table headers")
    rows = []
    for row in table[1:]:
        if len(row) != len(head):
            continue
        obj = dict(zip(head, row))
        try:
            date = datetime.strptime(obj["Game Date"], "%b %d, %Y")
            stats = {k: int(round(float(obj[k]))) for k in
                     ["MIN", "PTS", "FGM", "FGA", "3PM", "3PA", "FTM", "FTA", "REB", "AST"]}
        except (ValueError, KeyError):
            continue
        if any(v < 0 for v in stats.values()):
            continue
        if (stats["PTS"] != stats["FGM"] * 2 + stats["3PM"] + stats["FTM"]
                or stats["FGA"] < stats["3PA"] or stats["FGM"] < stats["3PM"]
                or stats["FTA"] < stats["FTM"]):
            raise ValueError("Official player box score failed score validation")
        rows.append({"date": date.strftime("%Y-%m-%d"), "matchup": obj["Matchup"],
                     "minutesRounded": stats["MIN"],
                     "PTS": stats["PTS"], "REB": stats["REB"], "AST": stats["AST"],
                     "3PM": stats["3PM"], "3PA": stats["3PA"],
                     "FGM": stats["FGM"], "FGA": stats["FGA"],
                     "FTM": stats["FTM"], "FTA": stats["FTA"]})
    if not 1 <= len(rows) <= 5:
        raise ValueError(f"Expected 1-5 verified recent games, got {len(rows)}")
    if len({r["date"] for r in rows}) != len(rows):
        raise ValueError("Duplicate player game dates")
    if rows != sorted(rows, key=lambda r: r["date"], reverse=True):
        raise ValueError("Player games not sorted newest first")
    return {
        "playerId": "1628973", "name": "Jalen Brunson",
        "season": "2026-27", "scope": "NBA.com last 5 displayed games only",
        "games": rows, "source": PLAYER_URL,
        "sourceType": "official NBA.com player profile"
    }

def read_json(path):
    try:
        return json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, ValueError):
        return None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous = read_json(OUT / "latest.json") or {"schema": 1, "season": "2026-27"}
    status = {"schema": 1, "checkedAtUtc": now, "provider": "NBA.com",
              "mode": "pilot", "sources": {}}
    updated = dict(previous)
    succeeded = 0
    for kind, url, parser in [
        ("team", TEAM_URL, parse_team),
        ("player", PLAYER_URL, parse_player)
    ]:
        try:
            obj = parser(fetch_page(url))
            obj["verifiedAtUtc"] = now
            updated[kind] = obj
            status["sources"][kind] = {"status": "verified", "url": url,
                                       "checkedAtUtc": now}
            succeeded += 1
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError,
                UnicodeError, OSError) as exc:
            err = f"{type(exc).__name__}: {str(exc)[:220]}"
            status["sources"][kind] = {"status": "unavailable", "url": url,
                                       "reason": err,
                                       "lastVerifiedAtUtc": previous.get(kind, {}).get("verifiedAtUtc")}
        time.sleep(1)
    if succeeded:
        updated["schema"] = 1
        updated["season"] = "2026-27"
        updated["lastSuccessfulRefreshUtc"] = now
        # Source failure does not change last verified data for that category.
        (OUT / "latest.json").write_text(json.dumps(updated, indent=2, sort_keys=True)+"\n")
    (OUT / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"verifiedSources": succeeded, "sourceChecks": status["sources"],
                      "dataPublished": bool(succeeded)}, indent=2))
    # A blocked source is informational, not a reason to publish fake data.
    # CI succeeds with status: unavailable, allowing inspection of its result.

if __name__ == "__main__":
    main()
