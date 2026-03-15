param(
    [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $ProjectRoot '.aiden-web.pid'
$baseUrl = "http://127.0.0.1:$Port"

$result = [ordered]@{
    pidFileExists = Test-Path $PidFile
    pid = $null
    processRunning = $false
    healthReachable = $false
    healthStatusCode = $null
    healthBody = $null
}

if ($result.pidFileExists) {
    $rawPid = (Get-Content $PidFile -Raw).Trim()
    if ($rawPid) {
        $result.pid = [int]$rawPid
        $proc = Get-Process -Id $result.pid -ErrorAction SilentlyContinue
        $result.processRunning = [bool]$proc
    }
}

try {
    $response = Invoke-WebRequest -UseBasicParsing "$baseUrl/health"
    $result.healthReachable = $true
    $result.healthStatusCode = $response.StatusCode
    $result.healthBody = $response.Content
}
catch {
    $result.healthReachable = $false
}

$result | ConvertTo-Json -Compress

if ($result.healthReachable) {
    exit 0
}

exit 1
