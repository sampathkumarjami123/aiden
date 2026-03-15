Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectRoot '.aiden-web.pid'

if (-not (Test-Path $PidFile)) {
    Write-Host 'No PID file found. Aiden web background server is not tracked.'
    exit 0
}

$rawPid = (Get-Content $PidFile -Raw).Trim()
if (-not $rawPid) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host 'PID file was empty and has been removed.'
    exit 0
}

$pidValue = [int]$rawPid
$proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (-not $proc) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "No running process found for PID $pidValue. Removed stale PID file."
    exit 0
}

Stop-Process -Id $pidValue -Force
Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Write-Host "Stopped Aiden web background server (PID $pidValue)."
