Write-Host "🚀 Starting local development environment..." -ForegroundColor Green

# Check if .env exists
if (!(Test-Path "backend\.env")) {
    Write-Host "⚠️  No .env file found. Creating from .example.env..." -ForegroundColor Yellow
    Copy-Item -Path ".example.env" -Destination "backend\.env"
    Write-Host "📝 Please update backend\.env with your Azure Storage credentials" -ForegroundColor Red
    exit 1
}

# Create virtual environment for Python
Write-Host "🐍 Creating Python virtual environment..." -ForegroundColor Yellow
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start backend in new window
Write-Host "🔧 Starting backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .\venv\Scripts\Activate.ps1; python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"

Set-Location ..

# Wait for backend to start
Start-Sleep -Seconds 5

# Start frontend in new window
Write-Host "🎨 Starting frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; npm run dev"

Set-Location ..

Write-Host "✅ Development environment is running!" -ForegroundColor Green
Write-Host "📍 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📍 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📍 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close the PowerShell windows to stop the services" -ForegroundColor Yellow