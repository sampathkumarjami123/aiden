#!/bin/bash
set -e

# AIDEN Azure Deployment Script (Bash version for Linux/WSL/macOS)

SUBSCRIPTION_ID="${1:-}"
LOCATION="${2:-eastus}"
RESOURCE_GROUP="${3:-aiden-rg}"
PROJECT_NAME="aiden"
OPENAI_API_KEY="${4:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_title() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ AIDEN Azure Deployment             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""
}

echo_step() {
    echo -e "${YELLOW}→ $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo_error() {
    echo -e "${RED}✗ $1${NC}"
}

echo_title

# Check prerequisites
echo_step "Checking prerequisites..."

command -v az >/dev/null 2>&1 || { echo_error "Azure CLI not found. Install from https://aka.ms/azurecli"; exit 1; }
echo_success "Azure CLI installed: $(az --version 2>&1 | head -1)"

command -v docker >/dev/null 2>&1 || { echo_error "Docker not found. Install from https://www.docker.com"; exit 1; }
echo_success "Docker installed: $(docker --version)"

# Azure login
echo_step "Authenticating with Azure..."
az account show > /dev/null 2>&1 || az login
echo_success "Authenticated"

# Set subscription
if [ -n "$SUBSCRIPTION_ID" ]; then
    az account set --subscription "$SUBSCRIPTION_ID"
else
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
fi
echo_success "Using subscription: $SUBSCRIPTION_ID"

# Create resource group
echo_step "Creating resource group: $RESOURCE_GROUP..."
if ! az group exists -n "$RESOURCE_GROUP" | grep -q true; then
    az group create -n "$RESOURCE_GROUP" -l "$LOCATION"
fi
echo_success "Resource group ready"

# Validate Bicep
echo_step "Validating Bicep templates..."
az bicep build --file infra/main.bicep --outdir infra
echo_success "Bicep validation complete"

# Deploy infrastructure
echo_step "Deploying Azure infrastructure (this may take 5-10 minutes)..."
DEPLOYMENT=$(az deployment sub create \
    --name "aiden-deployment-$(date +%s)" \
    --location "$LOCATION" \
    --template-file infra/main.bicep \
    --parameters projectName="$PROJECT_NAME" resourceGroupName="$RESOURCE_GROUP" openaiApiKey="$OPENAI_API_KEY")

ACR_SERVER=$(echo "$DEPLOYMENT" | jq -r '.properties.outputs.acrLoginServer.value')
CONTAINER_APP_URL=$(echo "$DEPLOYMENT" | jq -r '.properties.outputs.containerAppUrl.value')

echo_success "Infrastructure deployed"
echo -e "${BLUE}  ACR Server: $ACR_SERVER${NC}"
echo -e "${BLUE}  Container App URL: $CONTAINER_APP_URL${NC}"

# Build Docker image
echo_step "Building Docker image..."
docker build -t "$PROJECT_NAME:latest" .
echo_success "Docker image built"

# Push to ACR
echo_step "Pushing image to Azure Container Registry..."
ACR_NAME=$(echo "$ACR_SERVER" | cut -d'.' -f1)
az acr login --name "$ACR_NAME"
docker tag "$PROJECT_NAME:latest" "$ACR_SERVER/$PROJECT_NAME:latest"
docker push "$ACR_SERVER/$PROJECT_NAME:latest"
echo_success "Image pushed to ACR"

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║ Deployment Complete ✓              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your application is running at:${NC}"
echo -e "${BLUE}  🌐 https://$CONTAINER_APP_URL${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Open in browser: https://$CONTAINER_APP_URL"
echo "  2. Check logs: az containerapp logs show --resource-group $RESOURCE_GROUP --name $PROJECT_NAME-app-prod"
echo "  3. View metrics: Azure Portal → $RESOURCE_GROUP → Application Insights"
echo ""

# Save deployment info
cat > .azure/deployment.json <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "containerAppUrl": "$CONTAINER_APP_URL",
  "acrServer": "$ACR_SERVER",
  "resourceGroup": "$RESOURCE_GROUP",
  "location": "$LOCATION",
  "projectName": "$PROJECT_NAME"
}
EOF

echo_success "Deployment info saved to .azure/deployment.json"
