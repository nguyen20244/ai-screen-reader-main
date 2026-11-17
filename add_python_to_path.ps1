# Add Python to PATH permanently
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Adding Python to System PATH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python313"
$scriptsPath = "$env:LOCALAPPDATA\Programs\Python\Python313\Scripts"

Write-Host "Python installation found at: $pythonPath" -ForegroundColor Green
Write-Host ""

# Check if Python is already in PATH
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

if ($currentPath -notlike "*$pythonPath*") {
    Write-Host "Adding Python to user PATH..." -ForegroundColor Yellow
    
    try {
        # Add to user PATH
        $newPath = $currentPath + ";" + $pythonPath + ";" + $scriptsPath
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        
        Write-Host "✅ Python added to PATH successfully!" -ForegroundColor Green
        Write-Host "⚠️  You may need to restart your terminal/command prompt" -ForegroundColor Yellow
    }
    catch {
        Write-Host "❌ Failed to add Python to PATH: $_" -ForegroundColor Red
        Write-Host "You may need to run this as Administrator" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Python is already in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "Testing Python access..." -ForegroundColor Blue

# Test Python in current session
$env:PATH = $env:PATH + ";" + $pythonPath + ";" + $scriptsPath

try {
    $version = & "$pythonPath\python.exe" --version
    Write-Host "✅ Python version: $version" -ForegroundColor Green
} catch {
    Write-Host "❌ Python test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to install packages and start app!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$choice = Read-Host "Would you like to install packages and start the app now? (y/n)"

if ($choice -eq "y" -or $choice -eq "Y") {
    Write-Host ""
    Write-Host "Installing Python packages..." -ForegroundColor Blue
    
    & "$pythonPath\python.exe" -m pip install --upgrade pip
    & "$pythonPath\python.exe" -m pip install pillow pytesseract pyautogui opencv-python numpy openai anthropic python-dotenv
    
    Write-Host ""
    Write-Host "Testing components..." -ForegroundColor Blue
    & "$pythonPath\python.exe" test_components.py
    
    Write-Host ""
    Write-Host "Starting AI Screen Reader..." -ForegroundColor Green
    & "$pythonPath\python.exe" main.py
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
