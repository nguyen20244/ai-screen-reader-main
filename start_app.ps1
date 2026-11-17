# AI Screen Reader - PowerShell Startup Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Screen Reader - Starting Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python first:" -ForegroundColor Yellow
    Write-Host "1. Microsoft Store: ms-windows-store://pdp/?ProductId=9NRWMJP3717K" -ForegroundColor Yellow
    Write-Host "2. Or download from: https://python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env file created" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔑 Please edit .env file with your API keys:" -ForegroundColor Yellow
        Write-Host "- OpenAI: https://platform.openai.com/api-keys" -ForegroundColor Yellow
        Write-Host "- Anthropic: https://console.anthropic.com/" -ForegroundColor Yellow
        Write-Host ""
        
        $editChoice = Read-Host "Would you like to open .env file for editing now? (y/n)"
        if ($editChoice -eq "y" -or $editChoice -eq "Y") {
            notepad .env
            Write-Host "Please save the file after adding your API keys and press Enter to continue..."
            Read-Host
        }
    } else {
        Write-Host "❌ .env.example file not found" -ForegroundColor Red
        exit 1
    }
}

# Install dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Blue
try {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🔍 Running component tests..." -ForegroundColor Blue
try {
    python test_components.py
    Write-Host ""
    Write-Host "✅ Component tests completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Component tests had issues. You may need to:" -ForegroundColor Yellow
    Write-Host "- Install Tesseract OCR" -ForegroundColor Yellow
    Write-Host "- Add valid API keys to .env file" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Starting AI Screen Reader..." -ForegroundColor Green
Write-Host ""

try {
    python main.py
} catch {
    Write-Host "❌ Failed to start application" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "👋 Application closed" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
