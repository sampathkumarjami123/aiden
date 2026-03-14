Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe. Run .\\scripts\\setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $PythonExe -m unittest discover -s tests -p 'test_*.py' -v
}
finally {
    Pop-Location
}
