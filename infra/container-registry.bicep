param location string
param projectName string
param acrSku string = 'Basic'

// Create Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: replace('${projectName}acr', '-', '')
  location: location
  sku: {
    name: acrSku
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 30
        status: 'enabled'
      }
    }
  }
}

// Assign AcrPull role to managed identity (done at container-app level)

output loginServer string = acr.properties.loginServer
output resourceId string = acr.id
output registryName string = acr.name
