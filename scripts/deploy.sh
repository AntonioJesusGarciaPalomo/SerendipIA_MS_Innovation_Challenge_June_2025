#!/bin/bash

echo "🚀 Starting deployment process..."

# Check if azd is installed
if ! command -v azd &> /dev/null; then
    echo "❌ Azure Developer CLI (azd) is not installed."
    echo "Please install it from: https://aka.ms/azd-install"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo "🔐 Logging in to Azure..."
    az login
fi

# Initialize azd if not already done
if [ ! -f ".azure/config.json" ]; then
    echo "🔧 Initializing Azure Developer CLI..."
    azd init
fi

# Build frontend
echo "🏗️ Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Copy frontend build to backend
echo "📁 Copying frontend build to backend..."
mkdir -p backend/src/static
cp -r frontend/dist/* backend/src/static/

# Deploy with azd
echo "☁️ Deploying to Azure..."
azd up

echo "✅ Deployment complete!"
echo "Check the output above for your application URL."