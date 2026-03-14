param(
    [switch]$RecreateVenv,
    [switch]$SkipEnvFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot '.venv'
$PythonExe = Join-Path $VenvPath 'Scripts\python.exe'

Push-Location $ProjectRoot
try {
    if ($RecreateVenv -and (Test-Path $VenvPath)) {
        Write-Host 'Removing existing virtual environment...'
        Remove-Item -Recurse -Force $VenvPath
    }

    if (-not (Test-Path $PythonExe)) {
        Write-Host 'Creating virtual environment...'
        python -m venv .venv
    }

    if (-not (Test-Path $PythonExe)) {
        Write-Error "Unable to find virtual environment python at $PythonExe"
    }

    Write-Host 'Upgrading pip...'
    & $PythonExe -m pip install --upgrade pip

    Write-Host 'Installing dependencies...'
    & $PythonExe -m pip install -r requirements.txt

    if (-not $SkipEnvFile) {
        $envExample = Join-Path $ProjectRoot '.env.example'
        $envFile = Join-Path $ProjectRoot '.env'
        if ((Test-Path $envExample) -and (-not (Test-Path $envFile))) {
            Copy-Item $envExample $envFile
            Write-Host 'Created .env from .env.example'
        }
    }

    Write-Host 'Setup complete.'
    Write-Host 'Next steps:'
    Write-Host '  .\\scripts\\health-check.ps1'
    Write-Host '  .\\scripts\\start.ps1 -Mode web -Reload'
}
finally {
    Pop-Location
}
