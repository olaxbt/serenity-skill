# Serenity Twin — daily corpus refresh + radar brief (Windows Task Scheduler)
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/daily_brief.ps1
# Optional: register in Task Scheduler to run at 07:00 local time.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$Stamp = Get-Date -Format "yyyy-MM-dd"
$BriefDir = Join-Path $RepoRoot "corpus\data"
$BriefDated = Join-Path $BriefDir "daily-brief-$Stamp.txt"
$BriefLatest = Join-Path $BriefDir "daily-brief-latest.txt"
$LogFile = Join-Path $BriefDir "daily-brief.log"

function Write-Log {
    param([string]$Message)
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $Line -Encoding UTF8
    Write-Host $Line
}

Write-Log "=== daily_brief start (repo=$RepoRoot) ==="

# 1) Optional tweet sync + auto-distill (no-op if X_BEARER_TOKEN missing or sync disabled)
Write-Log "sync_tweets (optional)..."
try {
    python scripts/sync_tweets.py --include-replies --distill 2>&1 | Tee-Object -FilePath $LogFile -Append
} catch {
    Write-Log "sync_tweets warning: $_"
}

Write-Log "agent_distill --since-sync..."
try {
    python scripts/agent_distill.py --since-sync 2>&1 | Tee-Object -FilePath $LogFile -Append
} catch {
    Write-Log "agent_distill warning: $_"
}

# 2) Rebuild mention analytics (offline-safe)
Write-Log "rebuild_mentions..."
python scripts/rebuild_mentions.py 2>&1 | Tee-Object -FilePath $LogFile -Append

# 3) Radar snapshot
Write-Log "radar..."
$RadarOut = Join-Path $BriefDir "radar-snapshot-$Stamp.txt"
python scripts/radar.py --window 14 --top 12 2>&1 | Tee-Object -FilePath $RadarOut

# 4) Compose brief
$CorpusCount = "unknown"
$TweetsJson = Join-Path $BriefDir "tweets.json"
if (Test-Path $TweetsJson) {
    try {
        $raw = Get-Content $TweetsJson -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($raw -is [System.Array]) { $CorpusCount = $raw.Count }
        elseif ($raw.tweets) { $CorpusCount = $raw.tweets.Count }
    } catch {
        Write-Log "tweets.json count skipped: $_"
    }
}

$Header = @"
Serenity Twin — daily brief
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') local
Repo: $RepoRoot
Corpus tweets: $CorpusCount
Window: 14 days | Top: 12

--- Radar (scripts/radar.py) ---
"@

$RadarBody = Get-Content $RadarOut -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
if (-not $RadarBody) { $RadarBody = "(radar output empty - check daily-brief.log)" }

$Footer = @"

--- Next steps (Cursor Chat) ---
Ask: read corpus/data/daily-brief-latest.txt and summarize Heating tickers with corpus views.

--- Scripts run ---
sync_tweets.py --include-replies --distill
agent_distill.py --since-sync
rebuild_mentions.py
radar.py --window 14 --top 12
"@

$Full = $Header + "`n" + $RadarBody + "`n" + $Footer
Set-Content -Path $BriefDated -Value $Full -Encoding UTF8
Set-Content -Path $BriefLatest -Value $Full -Encoding UTF8

Write-Log "Wrote $BriefDated"
Write-Log "Wrote $BriefLatest"
Write-Log "=== daily_brief done ==="
