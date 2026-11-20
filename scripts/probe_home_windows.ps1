# Sports Bob NBA.com one-player residential connection probe
# Read-only: requests NBA.com and writes a local JSON report on your Desktop.
# No passwords, GitHub credentials, third-party estimates, or private data uploads.
$ErrorActionPreference = 'Stop'
$playerId = '1628973'
$season = '2026-27'
$headers = @{
    'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    'Accept' = 'application/json, text/plain, */*'
    'Accept-Language' = 'en-US,en;q=0.9'
    'Origin' = 'https://www.nba.com'
    'Referer' = 'https://www.nba.com/'
}
function Make-Url([string]$endpoint, [hashtable]$params) {
    $parts = foreach ($key in ($params.Keys | Sort-Object)) {
        $k = [Uri]::EscapeDataString([string]$key)
        $v = [Uri]::EscapeDataString([string]$params[$key])
        "$k=$v"
    }
    return ('https://stats.nba.com/stats/' + $endpoint + '?' + ($parts -join '&'))
}
function Verify-NbaRatings($json, [string]$name) {
    $groups = @()
    if ($null -ne $json.resultSets) { $groups = @($json.resultSets) }
    elseif ($null -ne $json.resultSet) { $groups = @($json.resultSet) }
    foreach ($group in $groups) {
        $keys = @($group.headers)
        $iOff = [array]::IndexOf($keys, 'OFF_RATING')
        $iDef = [array]::IndexOf($keys, 'DEF_RATING')
        $iNet = [array]::IndexOf($keys, 'NET_RATING')
        if ($iOff -lt 0 -or $iDef -lt 0 -or $iNet -lt 0) { continue }
        $iPlayer = [array]::IndexOf($keys, 'PLAYER_ID')
        $iSeason = [array]::IndexOf($keys, 'GROUP_VALUE')
        foreach ($row in @($group.rowSet)) {
            if ($null -eq $row) { continue }
            if ($iPlayer -ge 0 -and ([string]$row[$iPlayer]) -ne $playerId) { continue }
            if ($name -eq 'year_over_year' -and $iSeason -ge 0 -and ([string]$row[$iSeason]) -ne $season) { continue }
            [double]$off = 0
            [double]$def = 0
            [double]$net = 0
            if (-not [double]::TryParse([string]$row[$iOff], [ref]$off)) { continue }
            if (-not [double]::TryParse([string]$row[$iDef], [ref]$def)) { continue }
            if (-not [double]::TryParse([string]$row[$iNet], [ref]$net)) { continue }
            if ($off -le 0 -or $off -ge 250 -or $def -le 0 -or $def -ge 250 -or [math]::Abs($off - $def - $net) -gt 1.5) { continue }
            return @{
                offRating = $off; defRating = $def; netRating = $net
                playerId = $playerId; season = $season
                resultSet = [string]$group.name
            }
        }
    }
    return $null
}
$common = @{
    LeagueID='00'; Season=$season; SeasonType='Regular Season'; MeasureType='Advanced'
    PerMode='Totals'; LastNGames='0'; Month='0'; OpponentTeamID='0'; Period='0'
    PaceAdjust='N'; PlusMinus='N'; Rank='N'; DateFrom=''; DateTo=''
    GameSegment=''; Location=''; Outcome=''; SeasonSegment=''; VsConference=''; VsDivision=''
}
$leagueParams = $common.Clone()
foreach ($key in @('TeamID','TwoWay','PlayerExperience','PlayerPosition','College','Conference','Country','Division','DraftPick','DraftYear','GameScope','Height','Weight','ShotClockRange','StarterBench','PORound')) {
    $leagueParams[$key] = ''
}
$leagueParams['TeamID'] = '0'
$endpoints = @(
    @{ name='league_advanced'; url=(Make-Url 'leaguedashplayerstats' $leagueParams) },
)
foreach ($entry in @(
    @{ name='player_dashboard'; path='playerdashboardbygeneralsplits' },
    @{ name='year_over_year'; path='playerdashboardbyyearoveryear' }
)) {
    $p = $common.Clone()
    $p['PlayerID'] = $playerId
    $endpoints += @{name=$entry.name; url=(Make-Url $entry.path $p)}
}
$results = @()
foreach ($endpoint in $endpoints) {
    $test = @{ method=$endpoint.name; url=$endpoint.url; status='failed' }
    try {
        $json = Invoke-RestMethod -Uri $endpoint.url -Headers $headers -TimeoutSec 12 -Method Get
        $found = Verify-NbaRatings $json $endpoint.name
        if ($null -ne $found) {
            $test.status = 'verified_official'
            $test.ratings = $found
            Write-Host ("SUCCESS: " + $endpoint.name + "  OFFRTG " + $found.offRating + "  DEFRTG " + $found.defRating + "  NETRTG " + $found.netRating) -ForegroundColor Green
        } else {
            $test.status='responded_no_verified_rating_row'
            Write-Host ("RESPONSE, no usable ratings: " + $endpoint.name) -ForegroundColor Yellow
        }
    } catch {
        $test.error = $_.Exception.Message
        Write-Host ("FAILED: " + $endpoint.name + " - " + $test.error) -ForegroundColor Yellow
    }
    $results += $test
}
$pages = @(
    @{name='nba_player_html'; url='https://www.nba.com/stats/player/1628973/advanced?Season=2026-27'},
    @{name='nba_league_html'; url='https://www.nba.com/stats/players/advanced?Season=2026-27'}
)
foreach ($page in $pages) {
    $test = @{method=$page.name;url=$page.url;status='failed'}
    try {
        $res = Invoke-WebRequest -Uri $page.url -Headers $headers -TimeoutSec 12 -UseBasicParsing
        $test.status = 'html_loaded_not_accepted_as_verified_rating'
        $test.containsRatingFieldToken = ([string]$res.Content -match 'OFF_RATING|OFFRTG')
        Write-Host ("HTML loaded (not ratings verified): " + $page.name)
    } catch {
        $test.error = $_.Exception.Message
        Write-Host ("FAILED: " + $page.name + " - " + $test.error) -ForegroundColor Yellow
    }
    $results += $test
}
$successes = @($results | Where-Object { $_.status -eq 'verified_official' })
$report = @{
    playerName='Jalen Brunson'; playerId=$playerId
    season=$season; seasonType='Regular Season'
    source='NBA.com only'; checkedAtUtc=([DateTime]::UtcNow.ToString('o'))
    verifiedEndpoints=$successes.Count
    status=$(if ($successes.Count -gt 0) {'verified_official_api'} else {'unavailable'})
    attempts=$results
}
$desktop = [Environment]::GetFolderPath('Desktop')
if ([string]::IsNullOrWhiteSpace($desktop) -or -not (Test-Path $desktop)) { $desktop = (Get-Location).Path }
$reportPath = Join-Path $desktop 'sportsbob-nba-home-test.json'
$report | ConvertTo-Json -Depth 10 | Set-Content -Path $reportPath -Encoding UTF8
Write-Host ''
Write-Host ("Final official ratings status: " + $report.status)
Write-Host ("Report saved to " + $reportPath) -ForegroundColor Cyan
