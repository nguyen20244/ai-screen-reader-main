@echo off
echo ========================================
echo AI Screen Reader - Installation Script
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found!
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

echo Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please edit it with your API keys.
) else (
    echo .env file already exists.
)

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Install Tesseract OCR:
echo    - Download from: https://github.com/tesseract-ocr/tesseract/releases
echo    - Install and add to PATH
echo.
echo 2. Get API Keys:
echo    - OpenAI: https://platform.openai.com/api-keys
echo    - Anthropic: https://console.anthropic.com/
echo.
echo 3. Edit .env file with your API keys
echo.
echo 4. Run: python test_components.py (to test)
echo 5. Run: python main.py (to start the application)
echo.
pause
