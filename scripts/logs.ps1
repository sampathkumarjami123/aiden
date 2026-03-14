param(
    [int]$Tail = 100,
    [switch]$Follow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectRoot 'logs\aiden-web.log'

if (-not (Test-Path $LogFile)) {
    Write-Error "Log file not found at $LogFile. Start the web app and make a few API requests first."
}

if ($Follow) {
    Get-Content -Path $LogFile -Tail $Tail -Wait
}
else {
    Get-Content -Path $LogFile -Tail $Tail
}
