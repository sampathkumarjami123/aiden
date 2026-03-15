param(
    [ValidateSet('web', 'cli', 'desktop', 'voice', 'doctor')]
    [string]$Mode = 'web',
    [int]$Port = 8000,
    [switch]$Reload,
    [switch]$OpenBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe. Create the virtual environment first."
}

Push-Location $ProjectRoot
try {
    switch ($Mode) {
        'web' {
            if ($OpenBrowser) {
                Start-Process "http://127.0.0.1:$Port" | Out-Null
            }
            $args = @('-m', 'uvicorn', 'aiden_web:app', '--host', '127.0.0.1', '--port', "$Port")
            if ($Reload) {
                $args += '--reload'
            }
            & $PythonExe @args
        }
        'cli' {
            & $PythonExe 'aiden.py'
        }
        'desktop' {
            & $PythonExe 'aiden_desktop.py'
        }
        'voice' {
            & $PythonExe 'aiden_voice.py'
        }
        'doctor' {
            $baseUrl = "http://127.0.0.1:$Port"
            if ($OpenBrowser) {
                Start-Process $baseUrl | Out-Null
            }
            & (Join-Path $PSScriptRoot 'runtime-check.ps1') -BaseUrl $baseUrl
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }
        }
    }
}
finally {
    Pop-Location
}
