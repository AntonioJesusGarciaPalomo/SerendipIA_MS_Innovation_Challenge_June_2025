targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string

// Optional parameters
param resourceGroupName string = ''
param webAppName string = ''
param storageAccountName string = ''
param appServicePlanName string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

module storage './modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
  }
}

module appServicePlan './modules/app-service-plan.bicep' = {
  name: 'app-service-plan'
  scope: rg
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      tier: 'Basic'
    }
  }
}

module webApp './modules/web-app.bicep' = {
  name: 'web-app'
  scope: rg
  params: {
    name: !empty(webAppName) ? webAppName : '${abbrs.webSitesAppService}${resourceToken}'
    location: location
    tags: tags
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.12'
    appSettings: {
      AZURE_STORAGE_CONNECTION_STRING: storage.outputs.connectionString
      AZURE_STORAGE_CONTAINER_NAME: storage.outputs.containerName
      AZURE_STORAGE_ACCOUNT_NAME: storage.outputs.name
      AZURE_STORAGE_ACCOUNT_KEY: storage.outputs.accountKey
    }
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.name
output AZURE_STORAGE_CONTAINER_NAME string = storage.outputs.containerName
output AZURE_WEB_APP_NAME string = webApp.outputs.name
output AZURE_WEB_APP_URL string = webApp.outputs.url
