param name string
param location string = resourceGroup().location
param tags object = {}
param appServicePlanId string

@description('The runtime name')
param runtimeName string
@description('The runtime version')
param runtimeVersion string

@description('The app settings for configuration')
param appSettings object = {}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: name
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlanId
    siteConfig: {
      linuxFxVersion: '${toUpper(runtimeName)}|${runtimeVersion}'
      alwaysOn: false
      ftpsState: 'FtpsOnly'
      appSettings: [for setting in items(appSettings): {
        name: setting.key
        value: setting.value
      }]
      cors: {
        allowedOrigins: ['https://portal.azure.com', 'https://ms.portal.azure.com']
      }
    }
    httpsOnly: true
  }
}

output id string = webApp.id
output name string = webApp.name
output url string = 'https://${webApp.properties.defaultHostName}'
output defaultHostName string = webApp.properties.defaultHostName
