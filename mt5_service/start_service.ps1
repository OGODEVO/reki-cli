# MT5 API Service - Windows Startup Script
# Run this script to start the MT5 API service on Windows

Write-Host "Starting MT5 API Service..." -ForegroundColor Green

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Copy .env.example to .env and configure your MT5 credentials" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env file with your MT5 credentials, then run this script again" -ForegroundColor Yellow
    exit 1
}

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet

# Start the service
Write-Host "Starting FastAPI server on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python main.py
