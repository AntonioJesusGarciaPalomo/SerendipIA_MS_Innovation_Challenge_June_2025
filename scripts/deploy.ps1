Write-Host "🚀 Script de despliegue corregido para Azure App Service" -ForegroundColor Green

# Validar prerequisitos
Write-Host "🔍 Validando prerequisitos..." -ForegroundColor Yellow

# Verificar Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI versión: $($azVersion.'azure-cli')" -ForegroundColor Green
}
catch {
    Write-Host "❌ Azure CLI no encontrado. Instálalo desde: https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}

# Verificar login
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "✅ Conectado como: $($account.user.name)" -ForegroundColor Green
}
catch {
    Write-Host "🔐 Iniciando sesión en Azure..." -ForegroundColor Yellow
    az login
}

# Configurar variables
$resourceGroup = "rg-serendipia-dev"
$webAppName = "app-srzpfqfhfcazi"
$location = "West Europe"

Write-Host "🎯 Objetivo: $webAppName en $resourceGroup" -ForegroundColor Cyan

# 1. Construir frontend
Write-Host "🏗️ Construyendo frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Set-Location frontend
    npm install
    npm run build
    
    if (!(Test-Path "dist")) {
        Write-Host "❌ Error: No se generó el build del frontend" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Frontend construido exitosamente" -ForegroundColor Green
    Set-Location ..
} else {
    Write-Host "⚠️ Carpeta frontend no encontrada" -ForegroundColor Yellow
}

# 2. Preparar backend
Write-Host "📦 Preparando backend..." -ForegroundColor Yellow

# Crear directorio static en backend
New-Item -ItemType Directory -Force -Path "backend\src\static" | Out-Null

# Copiar build del frontend al backend
if (Test-Path "frontend\dist") {
    Copy-Item -Path "frontend\dist\*" -Destination "backend\src\static\" -Recurse -Force
    Write-Host "✅ Frontend copiado a backend/src/static/" -ForegroundColor Green
} else {
    Write-Host "⚠️ No se encontró build del frontend para copiar" -ForegroundColor Yellow
}

# 3. Crear archivo ZIP para despliegue
Write-Host "📦 Creando paquete de despliegue..." -ForegroundColor Yellow

# Limpiar ZIP anterior
if (Test-Path "deployment.zip") {
    Remove-Item "deployment.zip" -Force
}

# Ir al directorio backend y crear ZIP
Set-Location backend
Compress-Archive -Path ".\*" -DestinationPath "..\deployment.zip" -Force
Set-Location ..

Write-Host "✅ Paquete creado: deployment.zip" -ForegroundColor Green

# 4. Verificar y configurar Web App
Write-Host "⚙️ Configurando Azure App Service..." -ForegroundColor Yellow

# Verificar que la app existe
try {
    $webApp = az webapp show --name $webAppName --resource-group $resourceGroup --output json | ConvertFrom-Json
    Write-Host "✅ Web App encontrada: $($webApp.defaultHostName)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Web App no encontrada: $webAppName" -ForegroundColor Red
    exit 1
}

# Configurar runtime Python 3.12
Write-Host "🐍 Configurando Python 3.12..." -ForegroundColor Yellow
az webapp config set `
    --name $webAppName `
    --resource-group $resourceGroup `
    --linux-fx-version "PYTHON|3.12"

# Configurar comando de inicio
Write-Host "🚀 Configurando comando de inicio..." -ForegroundColor Yellow
az webapp config set `
    --name $webAppName `
    --resource-group $resourceGroup `
    --startup-file "startup.sh"

# Habilitar logging
Write-Host "📝 Habilitando logging..." -ForegroundColor Yellow
az webapp log config `
    --name $webAppName `
    --resource-group $resourceGroup `
    --application-logging filesystem `
    --level information

# Configurar variables de entorno
Write-Host "🔧 Configurando variables de entorno..." -ForegroundColor Yellow

# Obtener connection string del storage account
$storageAccountName = "stsrzpfqfhfcazi"
try {
    $storageKey = az storage account keys list `
        --resource-group $resourceGroup `
        --account-name $storageAccountName `
        --query "[0].value" `
        --output tsv
    
    $connectionString = "DefaultEndpointsProtocol=https;AccountName=$storageAccountName;AccountKey=$storageKey;EndpointSuffix=core.windows.net"
    
    az webapp config appsettings set `
        --name $webAppName `
        --resource-group $resourceGroup `
        --settings `
        "AZURE_STORAGE_CONNECTION_STRING=$connectionString" `
        "AZURE_STORAGE_CONTAINER_NAME=documents" `
        "AZURE_STORAGE_ACCOUNT_NAME=$storageAccountName" `
        "SCM_DO_BUILD_DURING_DEPLOYMENT=true" `
        "ENABLE_ORYX_BUILD=true" `
        "PRE_BUILD_COMMAND=echo 'Iniciando pre-build'" `
        "POST_BUILD_COMMAND=echo 'Build completado'"
    
    Write-Host "✅ Variables de entorno configuradas" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Error configurando storage. Continuando..." -ForegroundColor Yellow
}

# 5. Desplegar aplicación
Write-Host "☁️ Desplegando aplicación..." -ForegroundColor Yellow
az webapp deployment source config-zip `
    --name $webAppName `
    --resource-group $resourceGroup `
    --src "deployment.zip"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Despliegue completado exitosamente!" -ForegroundColor Green
    Write-Host "🌐 URL: https://$webAppName.azurewebsites.net/" -ForegroundColor Cyan
    Write-Host "📊 Panel de control: https://portal.azure.com/#@/resource/subscriptions/subscription/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$webAppName" -ForegroundColor Cyan
} else {
    Write-Host "❌ Error en el despliegue" -ForegroundColor Red
    exit 1
}

# 6. Verificar despliegue
Write-Host "🔍 Verificando despliegue..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "https://$webAppName.azurewebsites.net/api/health" -TimeoutSec 30
    $healthData = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ Health check exitoso:" -ForegroundColor Green
    Write-Host "   - Status: $($healthData.status)" -ForegroundColor White
    Write-Host "   - Service: $($healthData.service)" -ForegroundColor White
    
    Write-Host "🎉 ¡Aplicación desplegada y funcionando!" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Health check falló, pero la aplicación puede estar iniciando..." -ForegroundColor Yellow
    Write-Host "🔗 Verifica manualmente: https://$webAppName.azurewebsites.net/" -ForegroundColor Cyan
}

# 7. Mostrar logs en tiempo real (opcional)
$showLogs = Read-Host "¿Mostrar logs en tiempo real? (y/N)"
if ($showLogs -eq "y" -or $showLogs -eq "Y") {
    Write-Host "📋 Mostrando logs (Ctrl+C para detener)..." -ForegroundColor Yellow
    az webapp log tail --name $webAppName --resource-group $resourceGroup
}

Write-Host "🎯 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   Ver logs: az webapp log tail --name $webAppName --resource-group $resourceGroup" -ForegroundColor White
Write-Host "   Reiniciar: az webapp restart --name $webAppName --resource-group $resourceGroup" -ForegroundColor White
Write-Host "   SSH: az webapp ssh --name $webAppName --resource-group $resourceGroup" -ForegroundColor White

# Limpiar archivos temporales
Remove-Item "deployment.zip" -Force -ErrorAction SilentlyContinue

Write-Host "✨ Despliegue completado!" -ForegroundColor Green