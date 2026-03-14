# Azure CLI and Docker Installation Guide for AIDEN Deployment

## Prerequisites
- Windows 10/11 with admin access
- Internet connection

## Option 1: Install via Chocolatey (Recommended)

If you have Chocolatey installed:
```powershell
# Run PowerShell as Administrator, then:
choco install azure-cli -y
choco install docker-desktop -y
```

## Option 2: Install via Windows Package Manager (winget)

```powershell
winget install Microsoft.AzureCLI
winget install Docker.DockerDesktop
```

## Option 3: Manual Installation (Direct Downloads)

### Install Azure CLI
1. Download: https://aka.ms/azurecli
2. Run installer
3. Follow prompts
4. Restart PowerShell after installation

### Install Docker Desktop
1. Download: https://www.docker.com/products/docker-desktop
2. Run installer  
3. Enable WSL 2 backend (Windows Subsystem for Linux)
4. Restart computer after installation

## Verify Installations

After installation, open a NEW PowerShell window and run:

```powershell
# Check Azure CLI
az --version

# Check Docker
docker --version
```

## Next Steps

Once both are installed:
1. Run: `az login` to authenticate with Azure
2. Follow the deployment script in the terminal

## Troubleshooting

**"az command not found"**
- Close and reopen PowerShell
- Verify installation path in System Environment Variables
- Add C:\Program Files\Microsoft SDKs\Azure\CLI2\bin to PATH if needed

**Docker Desktop won't start**
- Enable virtualization in BIOS
- Update Windows to latest version
- Check Windows Subsystem for Linux (WSL 2) is installed

**Need WSL 2?**
```powershell
wsl --install
wsl --set-default-version 2
```

## Quick Start Command

After both tools are installed:
```powershell
cd "c:\Users\sampa\Videos\AIDEN\project 1"
az login
# Then run deployment commands
```
