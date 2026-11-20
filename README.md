# Sports Bob — NBA research data: official box scores + attributed advanced statistics

Free, public **NBA research data-only** repository for the private, downloadable Sports Bob HTML. This is **not** the original Sports Bob site.

## Current verified NBA data (2026–27)

As of the NBA.com collection on **November 19, 2026**:

| Category | Verified scope | Source |
| --- | --- | --- |
| Official NBA team averages and ranks | **30 / 30** teams | NBA.com individual team pages |
| Current NBA roster lists | **30 / 30** teams, 525 listed roster entries | NBA.com official team roster tables |
| Completed regular-season games | **222** games through November 18 | Dated NBA.com games pages + NBA-operated live-data final box-score files |
| Played-season player histories | **472** unique player IDs, **5,000** total player game appearances | NBA-operated official final box-score files |
| Individual NBA.com player profile averages | Six source-validated profiles | NBA.com player profiles |
| Independent on-court player net rating | **240 verified NBA player IDs** at initial collection | Hoops Nightly licensed on/off JSON (CC BY 4.0); *not NBA.com ratings* |
| Independently estimated team OFF / DEF / Net ratings | **30 / 30 teams** | BoxScore Lab current-season published CSV (CC BY 4.0); *not official NBA.com ratings* |

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
7. Check the licensed Hoops Nightly player on/off net-rating JSON; preserve last verified data on failure.
8. Check the BoxScore Lab 30-team OFF/DEF/Net rating CSV; preserve last verified data on failure.
9. Save source-specific timestamps and missing-data statuses.

After the GitHub Action finishes, open the **local Sports Bob HTML** and
press **Check latest data**. Its browser button downloads the saved data;
it does not start the GitHub collector.

The GitHub HTML refresh needs internet connectivity. It does not
need a paid sports-data API, a site editor, a backend login or hosting.

## Machine-readable public data

- [Official team stats](data/league/teams.json): NBA.com summary
  values plus NBA's displayed ranks.
- [Official rosters](data/league/rosters.json): names, positions, source, timestamp.
- [Independently published player on/off net ratings](data/league/onoff_ratings.json): 2026–27 on-court net rating, off-court net rating, published swing, playing time, and original source. Explicitly labeled *Hoops Nightly*, CC BY 4.0; these are **not** NBA.com official player or team ORtg/DRtg/NetRtg.
- [30-team published advanced estimates](data/league/team_advanced_estimates.json): provider-published offensive, defensive and net ratings, and pace, copied from [BoxScore Lab's free CC BY 4.0 CSV](https://boxscorelab.com/downloads/). Their methodology uses estimated possessions when required.
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

## Rating coverage and license

The free source [Hoops Nightly](https://hoopsnightly.com/api/open?part=on-off) makes its **original on/off dataset** reusable under [Creative Commons Attribution 4.0](https://hoopsnightly.com/data-license). It includes 240 current-season players at the first collection, each matched by the provider's official NBA numeric person ID. The HTML attributes the provider and links to the license. Its `on_net` is an on-court net points-per-100-possession measure, which is **not a player's individual scoring efficiency**. We copy the provider's number; Sports Bob does not calculate it.

**Published team estimates now available:** [BoxScore Lab](https://boxscorelab.com/methodology/) has a complete 30-team CC BY 4.0 CSV with season offense, defense and net ratings. Its possession denominators may be estimated by the independent publisher. Sports Bob copies the published values directly and identifies their origin; it does not generate new ratings.

**Still unavailable:** complete NBA.com official advanced ratings for all teams and players, and *all-player* offensive and defensive on-court ratings. Player net ratings cover 240 people from a different provider. An NBA.com official value is never replaced by an unlabeled third-party estimate.
