param location string
param projectName string
param environment string
param managedIdentityId string
param acrLoginServer string
param appInsightsInstrumentationKey string
param logAnalyticsWorkspaceId string
@secure()
param openaiApiKey string = ''
param containerImage string = '${acrLoginServer}/${projectName}:latest'
param containerPort int = 8000

// Create Container Apps Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-04-01-preview' = {
  name: '${projectName}-env-${environment}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: split(logAnalyticsWorkspaceId, '/')[8]
        sharedKey: reference(logAnalyticsWorkspaceId, '2022-10-01').defaultSharedKeys.primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    zoneRedundant: false
  }
}

// Create role assignment for managed identity to ACR
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: resourceGroup()
  name: guid(resourceGroup().id, managedIdentityId, 'acrpull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: reference(managedIdentityId, '2023-01-31').principalId
    principalType: 'ServicePrincipal'
  }
}

// Create Container App
resource containerApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
  name: '${projectName}-app-${environment}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      secrets: [
        {
          name: 'openai-api-key'
          value: openaiApiKey
        }
      ]
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentityId
        }
      ]
      ingress: {
        external: true
        targetPort: containerPort
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      dapr: {
        enabled: false
      }
    }
    template: {
      serviceBinds: []
      containers: [
        {
          image: containerImage
          name: projectName
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: 'InstrumentationKey=${appInsightsInstrumentationKey}'
            }
            {
              name: 'AIDEN_DEV_MODE'
              value: 'false'
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
          ]
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/'
                port: containerPort
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/'
                port: containerPort
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/'
                port: containerPort
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-requests'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [acrPullRoleAssignment]
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppId string = containerApp.id
output containerAppName string = containerApp.name
