param(
    [ValidateSet('web', 'cli', 'desktop', 'voice')]
    [string]$Mode = 'web',
    [int]$Port = 8000,
    [switch]$Reload
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
    }
}
finally {
    Pop-Location
}
