# Existing Sports Bob site — official NBA.com advanced ratings handoff

**Implementation status:** The source file, data adapter, and visual cards are committed and tested. **Not yet installed or deployed to the original owner-only Sports Bob D1 Staging site.** Its latest hosted source cannot be accessed through the connected tools in this conversation. Do not substitute the older Trading-Bots-Shilo dashboard or overwrite the existing authenticated site.

## Inputs
- [Official 473-player / 79-field November 20 snapshot](../data/league/official_player_advanced_2026_27.json).
- [Validated official Advanced data adapter](./official-advanced-adapter.js).
- [Read-only player and matchup cards](./official-advanced-cards.js).
- Source: NBA.com leaguedashplayerstats, 2026–27 regular season, MeasureType=Advanced, PerMode=PerGame, browser capture at 2026-11-20T06:42:29.498Z.
- Only OFF_RATING / DEF_RATING / NET_RATING as official ratings; never use estimated E_* values in their place or any third-party substitute.

## Minimal CURRENT-site integration

1. Get the actual most recently deployed authenticated site source and preserve its rollback and v71/v72+ features, D1 database, auth, archives, saved forecasts, research tools and all existing routes.
2. Add the two JavaScript modules above to the same site build; load the adapter before the cards. Bundle locally if the site's Content-Security-Policy blocks GitHub raw scripts or cross-origin data fetching.
3. Within the existing Player Research selected-player details, add a small container after the current stats strip. On selection of a verified NBA player ID, call:

    await SportsBobOfficialAdvancedCards.mountPlayer(existingAdvancedContainer, selectedNbaPlayerId);

4. Within the existing Matchup Research person-versus-person details, add an optional expandable container. For the selected verified player IDs, call:

    await SportsBobOfficialAdvancedCards.mountMatchup(existingMatchupContainer, firstNbaPlayerId, secondNbaPlayerId);

5. If the selected player is cleared, clear the corresponding container. The component protects against an older pending fetch replacing a newer selection.
6. Display the 'Frozen snapshot' date and NBA.com attribution. On-court team ratings are descriptive and do not alone imply an individual defensive matchup or an advantage. No modifications to projections, Picks Lab, archives, historical pregame features, game histories or official box scores.
7. Do not use this November 20 dataset in historical forecasts whose evidence cutoff predates November 20. Mark it later-observed descriptive context only.

## Verification before deployment

- Brunson (1628973): OFF 113.7, DEF 109.2, NET +4.5, USG 31.6%.
- Missing player ID displays unavailable.
- Matchup of Brunson (1628973) with Alperen Sengun (1630578) displays side-by-side without inventing an advantage.
- Rapid selection switching does not display stale cards.
- CSP and browser console are clear on actual staging site; test 390px mobile and 1440px desktop.
- All original authenticated tabs, Matchup Research, Opportunity Finder, Picks Lab, forecasts, archived games, saved findings and historical box scores function.
- Roll back current site version on critical regression. No production, database schema, trading or Kalshi changes.

## Current constraints

GitHub data-asset commits do **not** deploy to ChatGPT Sites or edit the owner-only Sports Bob D1 Staging application. With no site source/editor tool accessible here, these are drop-in changes prepared for the actual current site, not a claim that the hosted site is already updated. The Chrome collector was demonstrated once; it is a manual refresh, not unattended automation.
