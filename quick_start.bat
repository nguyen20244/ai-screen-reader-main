@echo off
echo ========================================
echo AI Screen Reader - Quick Start
echo ========================================
echo.
echo Your OpenAI API key is already configured!
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo.
    echo Please install Python first:
    echo 1. Press Windows + R
    echo 2. Type: ms-windows-store://pdp/?ProductId=9NRWMJP3717K
    echo 3. Press Enter and install Python 3.11
    echo.
    pause
    exit /b 1
)

echo ✅ Python is installed
echo.

echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install pillow pytesseract pyautogui opencv-python numpy openai anthropic python-dotenv

echo.
echo Testing your setup...
python test_components.py

echo.
echo ========================================
echo Ready to start!
echo ========================================
echo.
echo Press any key to start the AI Screen Reader...
pause >nul

python main.py
