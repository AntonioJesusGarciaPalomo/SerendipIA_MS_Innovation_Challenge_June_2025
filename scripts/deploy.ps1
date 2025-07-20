Write-Host "🚀 Starting deployment process..." -ForegroundColor Green

# Check if azd is installed
try {
    azd version | Out-Null
}
catch {
    Write-Host "❌ Azure Developer CLI (azd) is not installed." -ForegroundColor Red
    Write-Host "Please install it from: https://aka.ms/install-azd.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in to Azure
try {
    az account show | Out-Null
}
catch {
    Write-Host "🔐 Logging in to Azure..." -ForegroundColor Yellow
    az login
}

# Initialize azd if not already done
if (!(Test-Path ".azure\config.json")) {
    Write-Host "🔧 Initializing Azure Developer CLI..." -ForegroundColor Yellow
    azd init
}

# Build frontend
Write-Host "🏗️ Building frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
npm run build
Set-Location ..

# Copy frontend build to backend
Write-Host "📁 Copying frontend build to backend..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path backend\src\static | Out-Null
Copy-Item -Path frontend\dist\* -Destination backend\src\static\ -Recurse -Force

# Deploy with azd
Write-Host "☁️ Deploying to Azure..." -ForegroundColor Yellow
azd up

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Check the output above for your application URL." -ForegroundColor Cyan