param(
    [int]$Port = 8000,
    [int]$StartupTimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe. Create the virtual environment first."
}

Write-Host 'Checking Python environment...'
& $PythonExe --version

Write-Host 'Running syntax compile check...'
& $PythonExe -m compileall aiden.py aiden_core.py aiden_web.py aiden_desktop.py aiden_voice.py
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Compile check failed.'
}

Write-Host "Starting temporary web server on port $Port..."
$server = Start-Process -FilePath $PythonExe -WorkingDirectory $ProjectRoot -ArgumentList @('-m', 'uvicorn', 'aiden_web:app', '--host', '127.0.0.1', '--port', "$Port") -PassThru

try {
    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    $response = $null

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $response -or $response.StatusCode -ne 200) {
        Write-Error "Health endpoint did not become ready within $StartupTimeoutSeconds seconds."
    }

    Write-Host "Health check passed with HTTP $($response.StatusCode)."
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force
        Write-Host 'Stopped temporary web server.'
    }
}

Write-Host 'All checks passed.'
