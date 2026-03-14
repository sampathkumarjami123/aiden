param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [switch]$PushTag,
    [switch]$SkipChecks,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$GitArgs
    )

    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($GitArgs -join ' ')"
    }
}

Push-Location $ProjectRoot
try {
    if ($Version -notmatch '^v\d+\.\d+\.\d+$') {
        throw 'Version must follow semantic format: vMAJOR.MINOR.PATCH (example: v1.0.0).'
    }

    $status = git status --porcelain
    if ($status) {
        throw 'Working tree is not clean. Commit or stash changes before releasing.'
    }

    Invoke-Git fetch --tags origin

    $existingTag = git tag --list $Version
    if ($existingTag) {
        throw "Tag already exists: $Version"
    }

    if (-not $SkipChecks) {
        Write-Host 'Running quality gate before tagging...'
        & (Join-Path $ProjectRoot 'scripts\quality-gate.ps1')
        if ($LASTEXITCODE -ne 0) {
            throw 'Quality gate failed. Release aborted.'
        }
    }

    if ($DryRun) {
        Write-Host "Dry run succeeded. Would create tag: $Version"
        if ($PushTag) {
            Write-Host 'Dry run note: --PushTag was set; tag push skipped.'
        }
        return
    }

    Invoke-Git tag -a $Version -m "Release $Version"
    Write-Host "Created tag: $Version"

    if ($PushTag) {
        Invoke-Git push origin $Version
        Write-Host "Pushed tag: $Version"
    }
    else {
        Write-Host "Tag created locally. Push when ready: git push origin $Version"
    }
}
finally {
    Pop-Location
}
