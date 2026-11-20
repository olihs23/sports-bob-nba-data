# Sports Bob — NBA five-man lineup data (2026–27)

## Coverage
- **30 NBA teams**; **3974 distinct five-player groups**.
- **173 strictly audited games** out of 226 available saved official box scores; excluded 53 games with unresolved on-court ambiguities.
- Data assembled through 2026-11-20T19:58:17.724576+00:00 UTC. Not full season coverage.

## Source and labeling
- Input data: NBA-operated official final game box scores and NBA-operated play-by-play events.
- **Computed from NBA-owned records; not the NBA.com published lineup table.**
- OFF rating is calculated: points for / counted NBA-PBP lineup offensive possessions × 100.
- DEF rating is calculated: points against / counted NBA-PBP lineup defensive possessions × 100.
- NET is OFF minus DEF. Because the possession accounting is reconstructed, these numbers may differ from published NBA.com advanced ratings.
- Minutes, points, shot attempts, rebounds and turnovers are also allocated from published NBA events.
- Every accepted game was checked against official player game plus/minus, and games failing that check were excluded.
- **Do not represent these as official NBA-published advanced ratings or full-season lineups.**
- No third-party statistics or estimated provider ratings were used.

## Files
- `ALL_TEAMS_FIVE_MAN_LINEUPS.csv`: Excel-friendly league table.
- `manifest.json`: game-level failures, methodology and coverage.
- `TEAM.json`: one file per team with full precision.
- `SportsBob_2026-27_NBA_Five_Man_Data.zip`: portable bundle.
