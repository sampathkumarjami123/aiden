param(
    [string]$BaseUrl = 'http://127.0.0.1:8000'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Show-Guidance {
    param([string]$ErrorText)

    $msg = ($ErrorText | Out-String).ToLowerInvariant()
    Write-Section 'Guidance'

    if ($msg -match 'insufficient_quota|quota|ratelimiterror') {
        Write-Host 'OpenAI quota/billing is blocking live model access.' -ForegroundColor Yellow
        Write-Host '1) Enable billing or add credit in OpenAI project.'
        Write-Host '2) Wait 1-2 minutes.'
        Write-Host '3) Run this script again.'
        return
    }

    if ($msg -match 'invalid_api_key|authentication|unauthorized') {
        Write-Host 'API key appears invalid or unauthorized.' -ForegroundColor Yellow
        Write-Host '1) Generate a new key.'
        Write-Host '2) Update OPENAI_API_KEY in .env.'
        Write-Host '3) Restart the web app.'
        return
    }

    Write-Host 'Model is not live. Check Runtime Details in the app or run Retest Model.' -ForegroundColor Yellow
}

try {
    Write-Section 'Health'
    $health = Invoke-RestMethod -Method Get "$BaseUrl/health"
    Write-Host ("Service: {0} | OK: {1}" -f $health.service, $health.ok)

    Write-Section 'State'
    $state = Invoke-RestMethod -Method Get "$BaseUrl/api/state"
    $runtime = $state.runtime
    Write-Host ("Mode: {0}" -f $runtime.mode_label)
    Write-Host ("Has Model: {0}" -f $runtime.has_model)

    Write-Section 'Retest Model'
    $retest = Invoke-RestMethod -Method Post "$BaseUrl/api/runtime/retest"
    $runtime = $retest.runtime
    Write-Host ("Mode: {0}" -f $runtime.mode_label)
    Write-Host ("Has Model: {0}" -f $runtime.has_model)

    if ($runtime.model_error) {
        Write-Host ""
        Write-Host 'Last Error:' -ForegroundColor DarkYellow
        Write-Host $runtime.model_error
    }

    if ($runtime.mode_label -eq 'live' -and $runtime.has_model -eq $true) {
        Write-Host ""
        Write-Host 'Live model is active.' -ForegroundColor Green
        exit 0
    }

    Show-Guidance -ErrorText ($runtime.model_error | Out-String)
    exit 1
}
catch {
    Write-Host ''
    Write-Host 'Runtime check failed.' -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
