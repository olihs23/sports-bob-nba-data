# Sports Bob — Official NBA research data

Free public **NBA research data-only** repository for the separate, downloadable Sports Bob HTML. This is **not** the original hosted Sports Bob site.

## Official NBA data (2026–27)

Last documented NBA.com collection: **November 19, 2026**. Counts describe that checkpoint; consult the saved manifests for later updates.

| Category | Verified scope at checkpoint | Source |
| --- | --- | --- |
| Official NBA team averages and ranks | 30 / 30 teams | NBA.com individual team pages |
| Current NBA roster lists | 30 / 30 teams, 525 roster entries | NBA.com official team roster tables |
| Completed regular-season games | 222 games through November 18 | NBA.com game pages + NBA-operated final box scores |
| Played-season player histories | 472 player IDs, 5,000 player-game appearances | NBA-operated final box scores |
| Individual NBA.com player profile averages | Six source-validated profiles | NBA.com player profiles |
| Official player OFFRTG, DEFRTG, NETRTG | **Not yet collected** | Awaiting verified NBA.com advanced source |
| Official team OFFRTG, DEFRTG, NETRTG | **Not yet collected** | Awaiting verified NBA.com advanced source |

Four scheduled November 19 game sources returned HTTP 403 at collection time; they were not counted as final games. The source coverage manifest records failures.

**Policy:** Do not fetch, store, display or substitute independent provider estimates or third-party on/off ratings as Sports Bob advanced ratings. On November 19, 2026, the prior independent rating JSON files and both collector scripts were deleted from the active repository, and their scheduled refresh steps were removed. They are not restored on collector failure. Old Git commits and previously downloaded HTML copies can retain historical contents.

## Refresh verified NBA research data

[**Refresh all verified NBA research data**](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/refresh-all.yml)

The workflow may run manually on `main` and is scheduled every six hours (best effort):

1. Read NBA.com team profiles and published ranks.
2. Read NBA.com team roster tables.
3. Verify six NBA.com player profile summaries.
4. Read dated regular-season game listings since October 20, 2026.
5. Import missing completed official NBA final box scores.
6. Rebuild the season game index and player game logs.
7. Save official source-specific timestamps, coverage and missing-data statuses.

The browser's **Check latest data** button downloads saved records; it does not start the GitHub collector. It will not update already-downloaded HTML code or remove browser-cached copies by itself.

## Official NBA advanced-rating pilot

[**Test official NBA ratings for one player**](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/probe-official-advanced.yml)

This is a separate diagnostic, not a ratings data feed. It targets **Jalen Brunson (NBA player ID 1628973)** for the **2026–27 regular season**, attempting several NBA.com official API routes and the NBA.com advanced-stat profile webpage. The diagnostic accepts only source-verified NBA fields `OFF_RATING`, `DEF_RATING`, and `NET_RATING`; errors are recorded as failures, not filled with guesses. Successful checks are not yet automatically integrated into the website or the refresh workflow.

## Machine-readable official data

- [Official team stats](data/league/teams.json): NBA.com summary stats and published ranks.
- [Official rosters](data/league/rosters.json): names, positions, source and timestamp.
- [NBA individual profile pilot](data/league/players.json): six individual NBA.com profiles.
- [Completed season game index](data/season/index.json): game IDs, dates, teams and scores.
- [Full season player game logs](data/season/players.json): actual player box-score records.
- [Original NBA per-game files](data/season/games/): verified NBA final box scores.
- [Collection coverage and failures](data/season/manifest.json).
- [Official team check status](data/league/status.json) and [player check status](data/league/players_status.json).

## Integrity

- Games are matched by official NBA game ID and must be final.
- Player IDs and game statistics come from the official final box score.
- Points are checked against 2PM, 3PM and FTM; makes cannot exceed attempts.
- Blocked requests and unavailable advanced metrics are never fabricated.
- A failed refresh retains previously verified official records, not unofficial substitutes.
- 2026–27 regular season only; no old head-to-head results drive matchup assessments.
- Source-specific times distinguish last verification from time of viewing.

**Not yet collected:** official live injury statuses, verified projected starters, complete official advanced player/team ratings, complete lineup ratings and tracking/matchup data.

No paid APIs, private account secrets, trade execution or betting execution.
