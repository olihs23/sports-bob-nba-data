#!/usr/bin/env python3
"""Validate the official NBA.com player advanced snapshot; no network or third parties."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

DEFAULT = Path("data/league/official_player_advanced_2026_27.json")
REQUIRED = {
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION",
    "OFF_RATING", "DEF_RATING", "NET_RATING",
    "USG_PCT", "TS_PCT", "PACE", "AST_PCT", "REB_PCT",
}

def validate(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    src = doc.get("source", {})
    p = src.get("requestParameters", {})
    if doc.get("schemaVersion") != 1 or src.get("origin") != "https://stats.nba.com/stats/leaguedashplayerstats":
        raise ValueError("Not the intended NBA.com official-source snapshot")
    expected = {"Season": "2026-27", "SeasonType": "Regular Season",
                "MeasureType": "Advanced", "PerMode": "PerGame"}
    if any(p.get(k) != v for k, v in expected.items()):
        raise ValueError("Wrong NBA.com season/measure/filter")
    h = doc.get("headerColumns")
    rows = doc.get("rows")
    if not isinstance(h, list) or len(h) != 79 or len(set(h)) != 79:
        raise ValueError("Expected 79 unique NBA.com advanced fields")
    if not isinstance(rows, list) or not (400 <= len(rows) <= 750):
        raise ValueError("Missing or unreasonable player coverage")
    if doc.get("recordCount") != len(rows) or doc.get("columnCount") != len(h):
        raise ValueError("Declared coverage does not match row/column counts")
    names = set(h)
    if not REQUIRED.issubset(names):
        raise ValueError("Required NBA.com fields missing: " + repr(sorted(REQUIRED - names)))
    ix = {name: i for i, name in enumerate(h)}
    players, teams = set(), set()
    for n, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(h):
            raise ValueError(f"Wrong number of columns at row {n}")
        ident = row[ix["PLAYER_ID"]]
        if isinstance(ident, bool) or not isinstance(ident, int) or ident in players:
            raise ValueError(f"Duplicate or invalid player ID at row {n}")
        players.add(ident)
        teams.add(row[ix["TEAM_ID"]])
        off, deff, net = (row[ix[k]] for k in ("OFF_RATING", "DEF_RATING", "NET_RATING"))
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (off, deff, net)):
            raise ValueError(f"Missing or invalid official rating at row {n}")
        if abs(off - deff - net) > 0.11:
            raise ValueError(f"OFF/DEF/NET mismatch at row {n}")
    if len(teams) != 30:
        raise ValueError(f"Expected all 30 NBA teams, got {len(teams)}")
    metric_policy = doc.get("metricPolicy", {})
    if (metric_policy.get("offRating") != "OFF_RATING" or
        metric_policy.get("defRating") != "DEF_RATING" or
        metric_policy.get("netRating") != "NET_RATING" or
        metric_policy.get("estimatedMetricsNotSubstituted") is not True or
        metric_policy.get("noThirdPartyRatings") is not True):
        raise ValueError("Source policy missing or allows substitute ratings")
    return {"players": len(players), "teams": len(teams), "columns": len(h),
            "season": p["Season"], "source": src["origin"],
            "capturedAtUtc": src.get("capturedAtUtc"),
            "importedAtUtc": src.get("importedAtUtc")}

def main() -> int:
    arg = argparse.ArgumentParser()
    arg.add_argument("path", nargs="?", type=Path, default=DEFAULT)
    args = arg.parse_args()
    try:
        summary = validate(args.path)
        print("PASS: validated NBA.com official player advanced snapshot")
        print(json.dumps(summary, sort_keys=True))
        if not summary["capturedAtUtc"]:
            print("NOTE: original browser capture timestamp not supplied; this snapshot is frozen, not live")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        print("FAIL:", e, file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
