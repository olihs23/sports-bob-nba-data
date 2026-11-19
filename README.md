# Sports Bob — NBA official data refresh (free pilot)

Public **NBA statistics only**. The original private Sports Bob app, authentication,
saved forecasts, database and historical archives are not stored here.

## Status: real NBA.com retrieval proved, narrow pilot only

- Official [New York Knicks team profile](https://www.nba.com/team/1610612752/knicks):
  PPG, opponent PPG, RPG, APG and NBA.com's **published** ranks, *not recalculated ranks*.
- Official [Jalen Brunson player profile](https://www.nba.com/player/1628973/jalen-brunson):
  the latest **five displayed** box-score rows (not full season game logs).
- Every returned value is checked for correct identity, range, structure and
  source URL; Brunson game points must reconcile to FGM, 3PM and FTM.
- Failures are shown in `data/status.json`. The previous successful result
  remains in `data/latest.json`; blocked/missing sources are never replaced
  with made-up values.
- GitHub Actions runs automatically every **six hours** (schedule is best-effort).

This is an experimental free data route. NBA.com may return HTTP 403 from
GitHub Actions intermittently. A successful workflow run does **not**
guarantee the source data refreshed: read the source statuses.

## Refresh it yourself

1. Open [Refresh official NBA source pilot](https://github.com/olihs23/sports-bob-nba-data/actions/workflows/refresh-nba.yml).
2. Choose **Run workflow**, select `main`, and confirm.
3. When finished, check [Source status](data/status.json) and
   [Last verified data](data/latest.json).
4. In the downloaded Sports Bob HTML pilot, click **Load latest verified data**
   to download the latest successful result. This browser button reads JSON;
   it **does not trigger** GitHub Actions and needs an internet connection.

Raw JSON link for the HTML file:
`https://raw.githubusercontent.com/olihs23/sports-bob-nba-data/main/data/latest.json`

## Other first-party NBA source checks

- [Host reachability](data/host_checks.json) records which official NBA
  domains respond to GitHub's server. It is **not** a populated dataset
  or proof that advanced statistics or injury reports were parsed.
- Some first-party NBA CDN domains block cloud traffic with HTTP 403;
  the NBA-operated mediaops S3 endpoints responded during the pilot.
- Do not call a game schedule, player availability, a five-man lineup
  rating or fatigue value *verified* merely because a source URL exists.

## Next expansion gates

Expand to all 30 team profiles, then verified current-season player logs,
then NBA-hosted injury reports, pace/ratings, opponent shooting,
rebounding and actual five-man lineup analytics—**one independently
validated source at a time**. Only show the exact scopes successfully
retrieved and date each category separately. Never infer injury status,
team ranks, or lineup synergy from stale or partial data.

Python 3 standard library only; no paid API, tokens, secrets or dependencies.
