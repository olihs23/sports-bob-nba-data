# Sports Bob — official NBA research data

Free, public **NBA data-only** repository for the private, downloadable Sports Bob HTML. This is **not** the original Sports Bob site.

## Current verified NBA data (2026–27)

As of the NBA.com collection on **November 19, 2026**:

| Category | Verified scope | Source |
| --- | --- | --- |
| Official NBA team averages and ranks | **30 / 30** teams | NBA.com individual team pages |
| Current NBA roster lists | **30 / 30** teams, 525 listed roster entries | NBA.com official team roster tables |
| Completed regular-season games | **222** games through November 18 | Dated NBA.com games pages + NBA-operated live-data final box-score files |
| Played-season player histories | **472** unique player IDs, **5,000** total player game appearances | NBA-operated official final box-score files |
| Individual NBA.com player profile averages | Six source-validated profiles | NBA.com player profiles |

**Important:** Four scheduled November 19 game sources returned HTTP 403
at collection time. They were not counted as final games or presented as
results. Those sources will be retried on the next refresh. The coverage
manifest lists every checked date and failed request.

These are verified **per-game box score records**. We do not make up
player games, team ranks, lineup ratings, probabilities or fatigue levels.
For players outside the six individually sourced profile summaries,
we do not label calculated historical averages as official NBA.com
season averages.

## Just one refresh workflow

[**Refresh all verified NBA research data**](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/refresh-all.yml)

Select **Run workflow** on the `main` branch. The same workflow is
scheduled every six hours, best effort:

1. Read current official NBA.com team profiles and published ranks.
2. Read all 30 official NBA team roster tables.
3. Verify six current NBA.com player profile summaries.
4. Read every NBA.com dated regular-season game listing since
   October 20, 2026.
5. Import any missing completed **official NBA box scores**.
6. Rebuild the season games and player game logs from the verified records.
7. Save source-specific timestamps and missing-data statuses.

After the GitHub Action finishes, open the **local Sports Bob HTML** and
press **Check latest data**. Its browser button downloads the saved data;
it does not start the GitHub collector.

The GitHub HTML refresh needs internet connectivity. It does not
need a paid sports-data API, a site editor, a backend login or hosting.

## Machine-readable public data

- [Official team stats](data/league/teams.json): NBA.com summary
  values plus NBA's displayed ranks.
- [Official rosters](data/league/rosters.json): names, positions, source, timestamp.
- [NBA individual profile pilot](data/league/players.json): six players,
  last-five NBA.com profile rows and official summary averages.
- [Completed season game index](data/season/index.json): game IDs,
  dates, teams, final scores, original NBA sources.
- [Full season player game logs](data/season/players.json):
  player IDs and every played game with actual box-score statistics.
- [Original official per-game files](data/season/games/):
  one verified final NBA box score record per game.
- [Collection coverage and failures](data/season/manifest.json).
- [Official team check status](data/league/status.json)
  and [individual player check status](data/league/players_status.json).

## Integrity guarantees

- A final game must match its **official NBA game ID** and a
  dated official NBA.com game page; status must be Final.
- Actual player IDs and game statistics are taken from the **NBA box score**.
- Player points are verified against field goals, made threes and
  free throws. Makes cannot exceed attempts.
- Missing games and blocked requests are never fabricated.
- A collector failure cannot remove previously verified completed games.
- Source rankings and source-specific update times remain distinguishable
  from your browser's last GitHub read time.
- 2026–27 regular season only. No prior season records or legacy archived
  Sports Bob data are imported into these datasets.

**Not yet collected:** official live injury statuses, verified upcoming
starters, on-court five-man advanced ratings, or an actual physiological
fatigue measure. Those require separate first-party sources and will be
shown as unavailable until validated.

All code uses Python's standard library and free public GitHub Actions.
No paid API, leaked private account information or betting/trading action.
