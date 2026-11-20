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
| Official player OFFRTG, DEFRTG, NETRTG | **473 player rows (frozen November 20 capture)** | NBA.com `leaguedashplayerstats` Advanced API via owner's Chrome Network response |
| Official team OFFRTG, DEFRTG, NETRTG | **Not yet collected** | Awaiting verified NBA.com advanced source |

**Advanced ratings are a frozen NBA.com browser capture, NOT a live or GitHub-collected refresh.** The original capture timestamp was not provided; November 20, 2026 is the import date. NBA `OFF_RATING`, `DEF_RATING`, `NET_RATING` are preserved as distinct published fields; `E_*` estimate fields remain in the unmodified raw column set but must never substitute for the published ratings. A player's ratings describe team performance with that player on court, not individual offensive/defensive skill.

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

## Official advanced player snapshot — integration and refresh

- [Frozen official-source 473-player advanced JSON](data/league/official_player_advanced_2026_27.json) — 2026–27, Advanced, Regular Season, PerGame, all 79 original fields.
- [Research / Matchups JavaScript adapter](web/official-advanced-adapter.js) — checks the exact NBA source, accepts no third-party or substitute ratings, indexes players by NBA ID and teams, and returns descriptive comparisons without inventing matchup advantages.
- [Validator](scripts/validate_official_advanced.py) — rejects wrong seasons, missing players, bad rows or invalid ratings. [Validation workflow](.github/workflows/validate-official-advanced.yml) runs on changes to the snapshot and adapter.
- [Chrome browser collection Snippet](scripts/chrome_official_advanced_collector.js) — an **experimental, manually triggered** way to download a fresh validated dataset straight from NBA.com while viewing its advanced table. It has been offline-tested against the captured response; repeatable **live Chrome success has not yet been confirmed**.

### How to refresh using Chrome (no paid services)

1. On your home computer, open [NBA.com's 2026–27 Advanced Player Stats table](https://www.nba.com/stats/players/advanced?Season=2026-27) in Chrome. Confirm the player table loads.
2. Press **F12**, go to **Sources → Snippets** (find it in the Sources left sidebar), create a new Snippet named **SportsBob NBA official ratings**, and paste the full code from [chrome_official_advanced_collector.js](scripts/chrome_official_advanced_collector.js).
3. Run the Snippet from the NBA.com tab. If Chrome permits the request, it downloads **official_player_advanced_2026_27.json**, containing the official Advanced API's exact values and capture time.
4. In GitHub, replace [the frozen snapshot](data/league/official_player_advanced_2026_27.json) with the downloaded file using **Add file → Upload files** in the \`data/league/\` directory. The validation workflow checks the update; do not use it if the check fails.
5. If the Snippet reports a failed browser fetch, use the existing proven fallback: Chrome **Network → leaguedashplayerstats → Response → Copy response** and retain that NBA.com JSON. **Do not upload a raw response over the normalized snapshot** without converting and validating it first.

This is **not unattended automation**. Running GitHub's six-hour refresh workflow does *not* update this browser-captured dataset. Do not present the November 20 snapshot as live in any research interface.

### Connecting a specific HTML / Site

To use this data in a local Sports Bob HTML bundle, include the adapter's JS locally and call:

\`\`\`js
await SportsBobOfficialAdvanced.load();
const brunson = SportsBobOfficialAdvanced.getPlayer("1628973");
const team = SportsBobOfficialAdvanced.getTeamPlayers("NYK");
const comparison = SportsBobOfficialAdvanced.getMatchup("1628973", "1630578");
// comparison.advantage is deliberately null; descriptive only.
\`\`\`

The adapter has passed a 473-row read/lookup/reject-corruption smoke test. **The existing local v9 HTML file and hosted Sports Bob source are not in this repository**, so their actual Player Research / Matchups UI has not yet been modified or deployed. Connecting it into those screens requires the current interface source. No new site, database, trading route, or prediction logic is created here.

## Official NBA advanced-rating pilot

[**Test official NBA ratings for one player**](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/probe-official-advanced.yml)

This is a separate diagnostic, not a ratings data feed. It targets **Jalen Brunson (NBA player ID 1628973)** for the **2026–27 regular season**, attempting several NBA.com official API routes and the NBA.com advanced-stat profile webpage. The diagnostic accepts only source-verified NBA fields `OFF_RATING`, `DEF_RATING`, and `NET_RATING`; errors are recorded as failures, not filled with guesses. Successful checks are not yet automatically integrated into the website or the refresh workflow.

## Machine-readable official data

- [Official team stats](data/league/teams.json): NBA.com summary stats and published ranks.
- [Official rosters](data/league/rosters.json): names, positions, source and timestamp.
- [NBA individual profile pilot](data/league/players.json): six individual NBA.com profiles.
- [Official advanced player snapshot](data/league/official_player_advanced_2026_27.json): 473 NBA players and 79 NBA.com advanced columns, frozen browser capture.
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

**Not yet collected:** official live injury statuses, verified projected starters, official **team** advanced ratings, automated fresh player advanced ratings, complete lineup ratings and tracking/matchup data.

No paid APIs, private account secrets, trade execution or betting execution.
