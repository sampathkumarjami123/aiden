param(
    [ValidateSet('start', 'stop', 'status', 'doctor')]
    [string]$Action = 'status',
    [int]$Port = 8000,
    [switch]$Reload,
    [switch]$OpenBrowser,
    [switch]$Background
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $ScriptRoot 'start.ps1'
$StopScript = Join-Path $ScriptRoot 'stop-web.ps1'
$StatusScript = Join-Path $ScriptRoot 'status-web.ps1'

switch ($Action) {
    'start' {
        & $StartScript -Mode web -Port $Port -Reload:$Reload -OpenBrowser:$OpenBrowser -Background:$Background
        exit $LASTEXITCODE
    }
    'stop' {
        & $StopScript
        exit $LASTEXITCODE
    }
    'status' {
        & $StatusScript -Port $Port
        exit $LASTEXITCODE
    }
    'doctor' {
        & $StartScript -Mode doctor -Port $Port -OpenBrowser:$OpenBrowser
        exit $LASTEXITCODE
    }
}
