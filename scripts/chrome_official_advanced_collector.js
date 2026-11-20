/* Sports Bob: run as a saved Chrome DevTools Snippet ON https://www.nba.com/stats/players/advanced .
   Makes one NBA.com API request (up to one fallback attempt), validates official
   2026-27 Advanced values and downloads a file for manual GitHub upload.
   Does not request or export login cookies/tokens.
*/
(async function () {
  "use strict";
  if (!/(^|\.)nba\.com$/i.test(location.hostname)) {
    throw new Error("Open NBA.com/stats/players/advanced before running this Snippet.");
  }
  const params = {
    MeasureType: "Advanced", PerMode: "PerGame", PlusMinus: "N",
    PaceAdjust: "N", Rank: "N", LeagueID: "00", Season: "2026-27",
    SeasonType: "Regular Season", PORound: "0", Outcome: "",
    Location: "", Month: "0", SeasonSegment: "", DateFrom: "",
    DateTo: "", OpponentTeamID: "0", VsConference: "", VsDivision: "",
    TeamID: "0", Conference: "", Division: "", GameSegment: "",
    Period: "0", ShotClockRange: "", LastNGames: "0", GameScope: "",
    PlayerExperience: "", PlayerPosition: "", StarterBench: "",
    DraftYear: "", DraftPick: "", College: "", Country: "",
    Height: "", Weight: "", TwoWay: "", GameSubtype: "",
    ActiveRoster: "0", ISTRound: ""
  };
  // Prefer the precise URL seen in this browser, if exposed in Performance API.
  const seenUrls = [performance, ...Array.from(document.querySelectorAll("iframe")).flatMap(f => {
    try { return [f.contentWindow.performance]; } catch (_) { return []; }
  })].flatMap(perf => {
    try { return perf.getEntriesByType("resource").map(r => r.name); }
    catch (_) { return []; }
  });
  let url = seenUrls.find(u => u.startsWith("https://stats.nba.com/stats/leaguedashplayerstats?") &&
                               u.includes("MeasureType=Advanced") &&
                               u.includes("Season=2026-27")) || "";
  if (!url) {
    url = "https://stats.nba.com/stats/leaguedashplayerstats?" + new URLSearchParams(params).toString();
  }
  console.info("Sports Bob: checking one official NBA.com Advanced response...");
  let data = null, lastError = null;
  // The browser's CORS policy decides whether the same request can be made by a Snippet.
  for (const credentialMode of ["same-origin", "include"]) {
    try {
      const response = await fetch(url, {
        method: "GET", mode: "cors", credentials: credentialMode,
        cache: "no-store", headers: { Accept: "application/json, text/plain, */*" }
      });
      if (!response.ok) throw new Error("NBA.com returned HTTP " + response.status);
      data = await response.json();
      break;
    } catch (e) {
      lastError = e;
    }
  }
  if (!data) {
    console.error("NBA.com browser fetch failed. Use Network → leaguedashplayerstats → Response → Copy response as manual fallback.", lastError);
    throw new Error("NBA.com browser API fetch unavailable: " + String(lastError));
  }
  const info = data.parameters;
  if (data.resource !== "leaguedashplayerstats" ||
      info?.MeasureType !== "Advanced" || info?.Season !== "2026-27" ||
      info?.SeasonType !== "Regular Season" || info?.PerMode !== "PerGame") {
    throw new Error("Wrong NBA.com endpoint, season or filters; no file exported");
  }
  const block = data.resultSets?.find(s => s.name === "LeagueDashPlayerStats");
  const headers = block?.headers, rows = block?.rowSet;
  if (!Array.isArray(headers) || headers.length !== 79 ||
      !Array.isArray(rows) || rows.length < 400 || rows.length > 750) {
    throw new Error("NBA.com advanced response incomplete; no file exported");
  }
  const idx = Object.fromEntries(headers.map((h, i) => [h, i]));
  const required = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "OFF_RATING",
    "DEF_RATING", "NET_RATING", "USG_PCT", "TS_PCT"];
  if (required.some(k => idx[k] === undefined)) {
    throw new Error("Official advanced fields missing; no file exported");
  }
  const ids = new Set(), teamIds = new Set();
  for (const row of rows) {
    if (!Array.isArray(row) || row.length !== headers.length ||
        !Number.isInteger(row[idx.PLAYER_ID]) || ids.has(row[idx.PLAYER_ID])) {
      throw new Error("Duplicate player or malformed row; no file exported");
    }
    ids.add(row[idx.PLAYER_ID]);
    teamIds.add(row[idx.TEAM_ID]);
    const off = row[idx.OFF_RATING], def = row[idx.DEF_RATING], net = row[idx.NET_RATING];
    if (![off, def, net].every(Number.isFinite) || Math.abs(off - def - net) > 0.11) {
      throw new Error("Invalid OFF/DEF/NET rating fields; no file exported");
    }
  }
  if (teamIds.size !== 30) throw new Error("Missing NBA team data; no file exported");
  const encoded = new TextEncoder().encode(JSON.stringify(data));
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  const sha256 = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
  const exportData = {
    schemaVersion: 1,
    dataset: "NBA.com 2026-27 regular season player advanced statistics (browser-captured)",
    source: {
      origin: "https://stats.nba.com/stats/leaguedashplayerstats",
      resource: "leaguedashplayerstats",
      provenance: "Browser capture from NBA.com (Chrome DevTools Snippet)",
      capturedAtUtc: new Date().toISOString(),
      importedAtUtc: null,
      requestParameters: info,
      sourceFileSha256: sha256
    },
    recordCount: rows.length,
    columnCount: headers.length,
    headerColumns: headers,
    rows,
    metricPolicy: {
      offRating: "OFF_RATING",
      defRating: "DEF_RATING",
      netRating: "NET_RATING",
      estimatedMetricsNotSubstituted: true,
      noThirdPartyRatings: true
    },
    verification: {
      allRowsHaveCorrectColumnCount: true,
      uniquePlayerIds: ids.size,
      distinctTeams: teamIds.size,
      allMainRatingsPresent: true,
      mainRatingArithmeticValidWithinRounding: true
    }
  };
  const blob = new Blob([JSON.stringify(exportData)], { type: "application/json" });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = "official_player_advanced_2026_27.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 3000);
  const brunson = rows.find(row => row[idx.PLAYER_ID] === 1628973);
  console.info("Sports Bob: official NBA.com file downloaded", {
    players: rows.length, teams: teamIds.size, columns: headers.length,
    capturedAtUtc: exportData.source.capturedAtUtc,
    brunson: brunson ? {
      OFF_RATING: brunson[idx.OFF_RATING],
      DEF_RATING: brunson[idx.DEF_RATING],
      NET_RATING: brunson[idx.NET_RATING]
    } : "not in response"
  });
})().catch(err => console.error("Sports Bob advanced refresh failed:", err.message));
