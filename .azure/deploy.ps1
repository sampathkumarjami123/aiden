#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AIDEN Application Deployment Script for Azure Container Apps
.DESCRIPTION
    Deploys AIDEN FastAPI application to Azure with all infrastructure
.PARAMETER subscriptionId
    Azure Subscription ID
.PARAMETER location
    Azure region (default: eastus)
.PARAMETER resourceGroup
    Resource group name (default: aiden-rg)
#>

param(
    [string]$subscriptionId = "",
    [string]$location = "eastus",
    [string]$resourceGroup = "aiden-rg",
    [string]$projectName = "aiden",
    [string]$openaiApiKey = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Title {
    param([string]$text)
    Write-Host "`n" -ForegroundColor Black
    Write-Host "╔$(('═' * ($text.Length + 2)))╗" -ForegroundColor Cyan
    Write-Host "║ $text ║" -ForegroundColor Cyan
    Write-Host "╚$(('═' * ($text.Length + 2)))╝" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$text, [int]$step = 0)
    if ($step -gt 0) {
        Write-Host "[$step] $text" -ForegroundColor Yellow
    } else {
        Write-Host "→ $text" -ForegroundColor Green
    }
}

function Write-Success {
    param([string]$text)
    Write-Host "✓ $text" -ForegroundColor Green
}

function Write-Error {
    param([string]$text)
    Write-Host "✗ $text" -ForegroundColor Red
}

try {
    Write-Title "AIDEN Azure Deployment"
    
    # Step 1: Verify prerequisites
    Write-Step "Verifying prerequisites..." 1
    
    # Check Azure CLI
    try {
        $azVersion = az version 2>&1 | ConvertFrom-Json
        Write-Success "Azure CLI installed: $($azVersion['azure-cli'])"
    } catch {
        Write-Error "Azure CLI not found. Install from: https://aka.ms/azurecli"
        exit 1
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker installed: $dockerVersion"
    } catch {
        Write-Error "Docker not found. Install from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    # Step 2: Azure login and subscription
    Write-Step "Authenticating with Azure..." 2
    
    $account = az account show 2>&1
    if ($null -eq $account) {
        Write-Host "Opening Azure login browser..." -ForegroundColor Cyan
        az login
    } else {
        $accountInfo = $account | ConvertFrom-Json
        Write-Success "Already authenticated as: $($accountInfo.user.name)"
    }
    
    # Set subscription
    if ($subscriptionId) {
        az account set --subscription $subscriptionId
        Write-Success "Using subscription: $subscriptionId"
    } else {
        $subInfo = az account show | ConvertFrom-Json
        $subscriptionId = $subInfo.id
        Write-Success "Using default subscription: $subscriptionId"
    }
    
    # Step 3: Create resource group
    Write-Step "Creating resource group: $resourceGroup..." 3
    
    $rgExists = az group exists -n $resourceGroup | ConvertFrom-Json
    if (-not $rgExists) {
        az group create -n $resourceGroup -l $location
        Write-Success "Resource group created"
    } else {
        Write-Success "Resource group already exists"
    }
    
    # Step 4: Validate Bicep files
    Write-Step "Validating Bicep templates..." 4
    
    if (Test-Path "infra/main.bicep") {
        Write-Host "Validating infra/main.bicep..." -ForegroundColor Cyan
        az bicep build --file infra/main.bicep --outdir infra 2>&1 | Where-Object { $_ -match "error|Error" } | ForEach-Object {
            Write-Error $_
        }
        Write-Success "Bicep validation complete"
    } else {
        Write-Error "infra/main.bicep not found"
        exit 1
    }
    
    # Step 5: Deploy infrastructure
    Write-Step "Deploying Azure infrastructure..." 5
    
    Write-Host "This may take 5-10 minutes..." -ForegroundColor Cyan
    
    $deployParams = @{
        location = $location
        projectName = $projectName
        resourceGroupName = $resourceGroup
        openaiApiKey = $openaiApiKey
    }
    
    $deployment = az deployment sub create `
        --name "aiden-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')" `
        --location $location `
        --template-file infra/main.bicep `
        --parameters $deployParams 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Deployment failed"
        Write-Host $deployment -ForegroundColor Red
        exit 1
    }
    
    $deploymentOutput = $deployment | ConvertFrom-Json
    $acrServer = $deploymentOutput.properties.outputs.acrLoginServer.value
    $containerAppUrl = $deploymentOutput.properties.outputs.containerAppUrl.value
    
    Write-Success "Infrastructure deployed successfully"
    Write-Host "  ACR Server: $acrServer" -ForegroundColor Cyan
    Write-Host "  Container App URL: $containerAppUrl" -ForegroundColor Cyan
    
    # Step 6: Build Docker image
    Write-Step "Building Docker image..." 6
    
    Write-Host "Building image: $projectName`:latest" -ForegroundColor Cyan
    docker build -t "$projectName`:latest" .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker build failed"
        exit 1
    }
    Write-Success "Docker image built"
    
    # Step 7: Push to ACR
    Write-Step "Pushing image to Azure Container Registry..." 7
    
    Write-Host "Logging in to ACR: $acrServer" -ForegroundColor Cyan
    az acr login --name $acrServer.Split('.')[0]
    
    $imageUri = "$acrServer/$projectName`:latest"
    Write-Host "Tagging image: $imageUri" -ForegroundColor Cyan
    docker tag "$projectName`:latest" $imageUri
    
    Write-Host "Pushing image..." -ForegroundColor Cyan
    docker push $imageUri
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Image push failed"
        exit 1
    }
    Write-Success "Image pushed to ACR"
    
    # Step 8: Deployment complete
    Write-Title "Deployment Complete ✓"
    
    Write-Host "`nApplication is now running at:" -ForegroundColor Green
    Write-Host "  🌐 $containerAppUrl" -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Green
    Write-Host "  1. Open in browser: https://$containerAppUrl"
    Write-Host "  2. Check logs: az containerapp logs show --resource-group $resourceGroup --name $projectName-app-prod"
    Write-Host "  3. View metrics: Visit Azure Portal → $resourceGroup → Application Insights"
    Write-Host "`n"
    
    # Save deployment info
    $deploymentInfo = @{
        timestamp = Get-Date -Format 'o'
        containerAppUrl = $containerAppUrl
        acrServer = $acrServer
        resourceGroup = $resourceGroup
        location = $location
        projectName = $projectName
    } | ConvertTo-Json
    
    $deploymentInfo | Out-File -FilePath ".azure/deployment.json" -Force
    Write-Success "Deployment info saved to .azure/deployment.json"
    
} catch {
    Write-Error "Deployment failed: $_"
    exit 1
}
