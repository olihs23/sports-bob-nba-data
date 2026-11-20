/* Sports Bob — official NBA.com advanced player snapshot adapter (no estimates).
   Load this file into the existing Sports Bob HTML; it does not modify the hosted site.
*/
(function (root) {
  "use strict";
  const DEFAULT_URL = "https://raw.githubusercontent.com/olihs23/sports-bob-nba-data/main/data/league/official_player_advanced_2026_27.json";
  const METRICS = [
    "OFF_RATING", "DEF_RATING", "NET_RATING", "USG_PCT", "TS_PCT",
    "EFG_PCT", "AST_PCT", "REB_PCT", "OREB_PCT", "DREB_PCT",
    "PACE", "PIE", "GP", "MIN", "POSS", "FGA_PG", "FGM_PG"
  ];
  let snapshot = null;
  let byId = new Map();
  let byTeam = new Map();

  function validate(data) {
    if (!data || data.schemaVersion !== 1 ||
        data.source?.origin !== "https://stats.nba.com/stats/leaguedashplayerstats" ||
        data.source?.requestParameters?.MeasureType !== "Advanced" ||
        data.source?.requestParameters?.Season !== "2026-27" ||
        data.source?.requestParameters?.SeasonType !== "Regular Season" ||
        data.source?.requestParameters?.PerMode !== "PerGame") {
      throw new Error("Not the expected NBA.com 2026-27 player advanced snapshot");
    }
    const fields = data.headerColumns, rows = data.rows;
    if (!Array.isArray(fields) || !Array.isArray(rows) ||
        fields.length !== 79 || rows.length < 400 ||
        data.columnCount !== fields.length || data.recordCount !== rows.length) {
      throw new Error("Incomplete NBA.com advanced snapshot");
    }
    const columns = Object.fromEntries(fields.map((field, i) => [field, i]));
    const needed = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", ...METRICS];
    if (needed.some(k => columns[k] === undefined)) {
      throw new Error("Required official NBA.com columns missing");
    }
    const seen = new Set(), teams = new Set();
    for (const row of rows) {
      if (!Array.isArray(row) || row.length !== fields.length ||
          !Number.isInteger(row[columns.PLAYER_ID]) || seen.has(row[columns.PLAYER_ID])) {
        throw new Error("Duplicate/invalid player record");
      }
      seen.add(row[columns.PLAYER_ID]);
      teams.add(row[columns.TEAM_ID]);
      const off = row[columns.OFF_RATING], def = row[columns.DEF_RATING],
            net = row[columns.NET_RATING];
      if (![off, def, net].every(Number.isFinite) || Math.abs(off - def - net) > 0.11) {
        throw new Error("Invalid official OFF/DEF/NET ratings");
      }
    }
    if (teams.size !== 30) throw new Error("Expected all 30 NBA teams");
    return columns;
  }

  function ingest(data) {
    const columns = validate(data); // Always validate before replacing a working snapshot.
    const nextIds = new Map(), nextTeams = new Map();
    for (const row of data.rows) {
      const raw = Object.fromEntries(data.headerColumns.map((h, i) => [h, row[i]]));
      const player = {
        playerId: String(raw.PLAYER_ID),
        playerName: raw.PLAYER_NAME,
        teamId: String(raw.TEAM_ID),
        team: raw.TEAM_ABBREVIATION,
        gamesPlayed: raw.GP,
        minutesPerGame: raw.MIN,
        metrics: Object.fromEntries(METRICS.map(k => [k, raw[k]])),
        source: "NBA.com — browser-captured official Advanced table",
        season: "2026-27",
        isLive: false
      };
      nextIds.set(player.playerId, player);
      for (const teamKey of [player.teamId, player.team]) {
        if (!nextTeams.has(teamKey)) nextTeams.set(teamKey, []);
        nextTeams.get(teamKey).push(player);
      }
    }
    snapshot = Object.freeze({
      playerCount: data.rows.length,
      teamCount: new Set(data.rows.map(r => r[columns.TEAM_ID])).size,
      columnCount: data.headerColumns.length,
      captureDate: data.source.capturedAtUtc || null,
      importedAtUtc: data.source.importedAtUtc || null,
      sourceUrl: data.source.origin,
      season: "2026-27",
      seasonType: "Regular Season",
      refreshMethod: "manual NBA.com browser capture",
      isLive: false,
      warning: "Ratings reflect TEAM performance while this player was on court, not isolated personal offense/defense."
    });
    byId = nextIds;
    byTeam = nextTeams;
    return snapshot;
  }

  async function load(url = DEFAULT_URL) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error("Official NBA snapshot HTTP " + response.status);
    return ingest(await response.json());
  }
  function getPlayer(id) { return byId.get(String(id)) || null; }
  function getTeamPlayers(team) { return (byTeam.get(String(team).toUpperCase()) || []).slice(); }
  function getMatchup(playerAId, playerBId) {
    const left = getPlayer(playerAId), right = getPlayer(playerBId);
    return {
      available: Boolean(left && right),
      left, right,
      isProjection: false,
      advantage: null,
      warning: "Side-by-side on-court ratings are descriptive only. Do not assign a personnel matchup advantage from these ratings alone."
    };
  }
  function getStatus() { return snapshot; }
  root.SportsBobOfficialAdvanced = Object.freeze({
    load, ingest, getPlayer, getTeamPlayers, getMatchup, getStatus, DEFAULT_URL
  });
})(typeof window !== "undefined" ? window : globalThis);
