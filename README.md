# Sports Bob — Official NBA Research Data (free)

A **public, read-only NBA.com data repository** that your private, downloaded
Sports Bob HTML can refresh from. No private Sports Bob source code or data here.

## Current verified scope — November 19, 2026

| Dataset | Coverage | Source | Notes |
| --- | --- | --- | --- |
| Team summary stats and NBA-published ranks | **30 of 30 teams** | Current NBA.com team profiles | PPG, opponent PPG, RPG, APG; actual NBA rank, not our calculations |
| Official roster names and positions | **30 of 30 teams** | NBA.com team roster tables | 525 roster listings; they do **not** prove game participation or availability |
| Current player profiles | **6 verified players** | NBA.com individual player profiles | Brunson, Anunoby, Towns, Hart, Bridges, Tatum |
| Game log rows | **Latest 5 displayed games per player** | NBA.com profile box-score table | **Not full 2026–27 season logs**; one player may be missing newest refresh if NBA blocks a request |
| Official player season summary | Only where present on player page | NBA.com player profile | Published PPG, RPG, APG, not derived from the latest five |

No injury statuses, confirmed next-game starters, position-by-position matchup
statistics, advanced lineup ratings, or complete season player game logs
have been collected yet. **Never label missing information as current.**

## One refresh link

[**Refresh all verified NBA research data**](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/refresh-all.yml)

- Click **Run workflow** to ask GitHub to fetch NBA.com again.
- It also runs automatically every six hours, as a best-effort GitHub schedule.
- The workflow collects 30 teams and their official rosters, then the six
  identity-verified player profiles, then saves the validated data.
- GitHub Actions runs on standard free hosted runners for this public repo.
- Sources can intermittently return HTTP 403. A failure does not erase the
  previously verified record; each source has its own `verifiedAtUtc`.

After that workflow finishes, open the downloaded Sports Bob HTML and press
**Check latest GitHub data**. That button reads the saved JSON, it does
**not** trigger GitHub Actions or NBA.com itself.

### Public JSON for your local HTML

- [Teams](data/league/teams.json) — official team stat values + NBA ranks
- [Official rosters](data/league/rosters.json) — names and positions
- [Player profiles](data/league/players.json) — six players' latest five games
- [Team and roster check status](data/league/status.json)
- [Per-player collection status](data/league/players_status.json)
- [Original one-team pilot](data/latest.json), kept for compatibility only

The HTML uses public raw GitHub links such as
`https://raw.githubusercontent.com/olihs23/sports-bob-nba-data/main/data/league/teams.json`.

## Integrity and safety rules

1. **Official NBA.com sources only.** No self-made league rankings or
   betting model, no extrapolated counts, no fake availability.
2. NBA.com ranks and season averages are **read directly** from the
   published team/player profile pages.
3. Player rows must reconcile PTS = 2×FGM + 3PM + FTM, and attempts
   cannot be less than makes.
4. An official roster **name** is not proof of a correct **player ID**.
   The site publishes no guessed person IDs; the known pilot identities
   were verified against their NBA.com profile pages.
5. A failed request is recorded separately and retains the last
   successfully verified entry.
6. Team statistics, roster membership, and player game logs have their own
   verification dates. Browser refresh is not a new NBA.com collection.

## Next steps — not yet completed

Expand validated player identity coverage beyond six players, then establish
an official NBA source for **full 2026–27 season box-score history** (not just
five displayed rows). Separately pilot current injury reports, schedules,
rest indicators, shooting defense and five-player lineup ratings.
Do not turn on any category without a verified source and safe failure mode.

Python 3 standard library only; zero paid sports-data APIs, subscriptions,
inference services, tokens or secrets.
