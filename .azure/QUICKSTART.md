# 🚀 AIDEN Azure Deployment - Quick Start Guide

## Status: Ready to Deploy ✅

Your AIDEN application is fully configured and ready for deployment to Azure. This guide will walk you through the deployment process.

---

## 📋 What You Need

### Prerequisites
- **Azure Account** - Free tier available at https://azure.microsoft.com/free/
- **Azure CLI** - Download from https://aka.ms/azurecli
- **Docker Desktop** - Download from https://www.docker.com/products/docker-desktop
- **Windows PowerShell 5.1+** or **Bash** (Linux/WSL/macOS)

### Installation Check
```powershell
# In PowerShell / Terminal
az --version
docker --version
```

If either command fails, install the missing tool first.

---

## 🎯 Deployment Steps

### Step 1: Install Required Tools (One-Time)

**Windows (PowerShell as Administrator):**
```powershell
# Using Chocolatey (if installed)
choco install azure-cli -y
choco install docker-desktop -y

# OR using Windows Package Manager
winget install Microsoft.AzureCLI
winget install Docker.DockerDesktop
```

**macOS / Linux:**
```bash
# macOS with Homebrew
brew install azure-cli
brew install docker

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
sudo apt install docker.io
```

After installation, **restart your terminal**.

### Step 2: Authenticate with Azure

```powershell
# PowerShell
az login

# Bash
az login
```

This opens your browser for Microsoft authentication. Sign in with your Azure account.

### Step 3: Deploy Using Script (Recommended)

**For Windows PowerShell:**
```powershell
cd "c:\Users\sampa\Videos\AIDEN\project 1"

# Run deployment script
.\.azure\deploy.ps1 -subscriptionId "YOUR_SUBSCRIPTION_ID" -location "eastus"
```

**For Bash (Linux/WSL/macOS):**
```bash
cd "/path/to/AIDEN/project 1"
chmod +x .azure/deploy.sh
./.azure/deploy.sh "YOUR_SUBSCRIPTION_ID" eastus
```

### Step 4: Deploy Manually (If Script Fails)

#### Create Resource Group
```powershell
# Set variables
$resourceGroup = "aiden-rg"
$location = "eastus"
$projectName = "aiden"

# Create group
az group create -n $resourceGroup -l $location
```

#### Deploy Infrastructure
```powershell
# Validate Bicep
az bicep build --file infra/main.bicep

# Deploy resources
az deployment sub create `
  --location $location `
  --template-file infra/main.bicep `
  --parameters `
    projectName=$projectName `
    resourceGroupName=$resourceGroup `
    environment="prod"
```

#### Build and Push Docker Image
```powershell
# Build image
docker build -t aiden:latest .

# Get ACR details from deployment output
$acrServer = "YOUR_ACR_SERVER.azurecr.io"

# Tag image
docker tag aiden:latest "$acrServer/aiden:latest"

# Login to ACR
az acr login --name $acrServer.Split('.')[0]

# Push image
docker push "$acrServer/aiden:latest"
```

---

## 📊 What Gets Deployed

| Component | Purpose | SKU |
|-----------|---------|-----|
| **Azure Container Apps** | Hosts your FastAPI app | Consumption (pay-per-request) |
| **Container Registry** | Stores Docker image | Basic |
| **Application Insights** | Monitors performance | Standard |
| **Log Analytics** | Centralizes logs | Pay-per-GB |
| **Managed Identity** | Secure authentication | Free |

**Estimated Monthly Cost**: $5-20 (depending on usage)

---

## ✅ Verify Deployment

After deployment completes:

```powershell
# Get deployment info
cat .azure/deployment.json

# Check container app status
az containerapp show -n aiden-app-prod -g aiden-rg

# View logs
az containerapp logs show -n aiden-app-prod -g aiden-rg --follow

# Get container app URL
az containerapp show -n aiden-app-prod -g aiden-rg --query properties.configuration.ingress.fqdn
```

---

## 🌐 Access Your App

Once deployed, your app is accessible at:
```
https://<your-app-name>.azurecontainerapps.io
```

**Features available:**
- ✅ 26 UI enhancements
- ✅ Theme selector (5 themes)
- ✅ Message bookmarks
- ✅ Conversation tagging
- ✅ Statistics dashboard
- ✅ Dark mode support
- ✅ And much more!

---

## 🔧 Configuration

### Environment Variables

Edit `.azure/deploy.ps1` or manually set in Azure Portal:

```powershell
# Optional: Add OpenAI API Key
$openaiApiKey = "sk-..."
```

**Available Settings:**
- `AIDEN_DEV_MODE=false` - Use API (default)
- `AIDEN_DEV_MODE=true` - Use local fallback (no API key)
- `OPENAI_API_KEY` - OpenAI API key (optional)

### Scaling

Container app auto-scales by default:
- **Min replicas**: 1
- **Max replicas**: 10
- **Scales up when**: CPU > 80%

To modify in the Azure Portal:
1. Go to Container Apps → aiden-app-prod
2. Click "Scale and replicas"
3. Adjust min/max as needed

---

## 📈 Monitoring

### View Logs
```powershell
# Real-time logs
az containerapp logs show -n aiden-app-prod -g aiden-rg --follow

# Last 100 entries
az containerapp logs show -n aiden-app-prod -g aiden-rg --tail 100
```

### Application Insights
1. Open Azure Portal
2. Go to Resource Group → aiden-rg
3. Click on Application Insights resource
4. View:
   - Performance metrics
   - Exception logs
   - Page views
   - Request duration

---

## 🐛 Troubleshooting

### Container won't start
**Error:** `Container initialization failed`
- Check logs: `az containerapp logs show -n aiden-app-prod -g aiden-rg`
- Verify Python requirements: `cat requirements.txt`
- Check Dockerfile: `cat Dockerfile`

### Image push fails
**Error:** `Unauthorized: image push operation denied`
```powershell
# Re-authenticate
az acr login --name <acr-name>
docker push <image-uri>
```

### DNS resolution issues
**Error:** `Failed to resolve <app-url>`
- Wait 30 seconds for DNS propagation
- Check Container App status: `az containerapp show ...`
- Verify ingress configuration in Azure Portal

### Out of memory
**Error:** `OOMKilled`
- Increase memory: Edit `infra/container-app.bicep` line 29
- Change `containerMemory` from `0.5Gi` to `1Gi`
- Redeploy

### Port binding failed
**Error:** `Port 8000 already in use`
- Update `container-app.bicep` to use different port
- Update Dockerfile EXPOSE and CMD

---

## 🗑️ Cleanup

To delete all Azure resources and stop billing:

```powershell
# Delete resource group (removes everything)
az group delete -n aiden-rg --yes

# Or individual resources
az acr delete -n aidenacr -r
az containerapp delete -n aiden-app-prod -g aiden-rg
```

---

## 📚 Useful Links

- **Azure Portal**: https://portal.azure.com
- **Container Apps Docs**: https://docs.microsoft.com/azure/container-apps
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Docker Docs**: https://docs.docker.com
- **Azure CLI Docs**: https://docs.microsoft.com/cli/azure

---

## 📞 Support

If you encounter issues:

1. **Check logs** first: `az containerapp logs`
2. **Review deployment errors** in Azure Portal
3. **Verify prerequisites** are installed
4. **Check Azure quotas** - may need quota increase
5. **Consult documentation links** above

---

## ✨ Next Steps After Deployment

1. **Share your app URL** - It's publicly accessible
2. **Monitor performance** - Check Application Insights
3. **Customize** - Modify features in `web/static/app.js`
4. **Scale** - Increase max replicas if needed
5. **Set custom domain** - Add your own domain name

---

**You're all set! 🎉 Your AIDEN application is ready to deploy to Azure.**

Questions? Check `.azure/plan.copilotmd` for detailed architecture info.
