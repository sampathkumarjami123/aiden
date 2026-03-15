param(
    [ValidateSet('web', 'cli', 'desktop', 'voice', 'doctor')]
    [string]$Mode = 'web',
    [int]$Port = 8000,
    [switch]$Reload,
    [switch]$OpenBrowser,
    [switch]$Background
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$WebPidFile = Join-Path $ProjectRoot '.aiden-web.pid'

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

            if ($Background) {
                $existingPid = if (Test-Path $WebPidFile) { (Get-Content $WebPidFile -Raw).Trim() } else { '' }
                if ($existingPid) {
                    $running = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
                    if ($running) {
                        Write-Error "Aiden web server appears to already be running (PID $existingPid). Run scripts/stop-web.ps1 first."
                    }
                    Remove-Item $WebPidFile -Force -ErrorAction SilentlyContinue
                }

                $proc = Start-Process -FilePath $PythonExe -ArgumentList $args -WorkingDirectory $ProjectRoot -PassThru
                Set-Content -Path $WebPidFile -Value $proc.Id -NoNewline

                $baseUrl = "http://127.0.0.1:$Port"
                $ready = $false
                for ($i = 0; $i -lt 20; $i++) {
                    Start-Sleep -Milliseconds 500
                    try {
                        $resp = Invoke-WebRequest -UseBasicParsing "$baseUrl/health"
                        if ($resp.StatusCode -eq 200) {
                            $ready = $true
                            break
                        }
                    }
                    catch {
                        # Continue probing until timeout.
                    }
                }

                if ($OpenBrowser) {
                    Start-Process $baseUrl | Out-Null
                }

                if ($ready) {
                    Write-Host "Aiden web server started in background (PID $($proc.Id)) at $baseUrl"
                }
                else {
                    Write-Warning "Background process started (PID $($proc.Id)) but health endpoint did not become ready in time."
                }
                break
            }

            if ($OpenBrowser) {
                Start-Process "http://127.0.0.1:$Port" | Out-Null
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
