param(
    [int]$Port = 8000,
    [int]$StartupTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot
try {
    Write-Host 'Running unit tests...'
    & (Join-Path $ProjectRoot 'scripts\test.ps1')

    Write-Host 'Running web health check...'
    & (Join-Path $ProjectRoot 'scripts\health-check.ps1') -Port $Port -StartupTimeoutSeconds $StartupTimeoutSeconds

    Write-Host 'Quality gate passed.'
}
finally {
    Pop-Location
}
