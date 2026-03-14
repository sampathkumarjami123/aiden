targetScope = 'subscription'

param location string = 'eastus'
param environment string = 'prod'
param projectName string = 'aiden'
param resourceGroupName string = 'aiden-rg'
param openaiApiKey string = ''

// Create resource group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
}

// Deploy all resources to the resource group
module identity './identity.bicep' = {
  scope: rg
  name: '${projectName}-identity'
  params: {
    location: location
    projectName: projectName
  }
}

module monitoring './monitoring.bicep' = {
  scope: rg
  name: '${projectName}-monitoring'
  params: {
    location: location
    projectName: projectName
    environment: environment
  }
}

module acr './container-registry.bicep' = {
  scope: rg
  name: '${projectName}-acr'
  params: {
    location: location
    projectName: projectName
    acrSku: 'Basic'
  }
}

module containerApp './container-app.bicep' = {
  scope: rg
  name: '${projectName}-app'
  params: {
    location: location
    projectName: projectName
    environment: environment
    managedIdentityId: identity.outputs.managedIdentityId
    acrLoginServer: acr.outputs.loginServer
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    openaiApiKey: openaiApiKey
  }
}

output containerAppUrl string = containerApp.outputs.fqdn
output acrLoginServer string = acr.outputs.loginServer
output managedIdentityClientId string = identity.outputs.managedIdentityClientId
