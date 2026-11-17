@echo off
echo ========================================
echo AI Screen Reader - Setup and Run
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Let me help you install it...
    echo.
    echo OPTION 1: Install from Microsoft Store (Recommended)
    echo 1. Press Windows key + R
    echo 2. Type "ms-windows-store://pdp/?ProductId=9NRWMJP3717K"
    echo 3. Press Enter to open Microsoft Store
    echo 4. Click "Install" to install Python 3.11
    echo.
    echo OPTION 2: Download from python.org
    echo 1. Go to https://python.org/downloads/
    echo 2. Download Python 3.8 or higher
    echo 3. Run installer and check "Add Python to PATH"
    echo.
    echo After installing Python, run this script again.
    pause
    exit /b 1
)

echo Python found! Version:
python --version
echo.

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Install packages one by one to see which ones fail
echo Installing Pillow...
python -m pip install pillow>=10.0.0

echo Installing pytesseract...
python -m pip install pytesseract>=0.3.10

echo Installing pyautogui...
python -m pip install pyautogui>=0.9.54

echo Installing opencv-python...
python -m pip install opencv-python>=4.8.0

echo Installing numpy...
python -m pip install numpy>=1.24.0

echo Installing openai...
python -m pip install openai>=1.0.0

echo Installing anthropic...
python -m pip install anthropic>=0.7.0

echo Installing python-dotenv...
python -m pip install python-dotenv>=1.0.0

echo.
echo Creating .env file if it doesn't exist...
if not exist .env (
    copy .env.example .env
    echo .env file created from template
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo IMPORTANT: Setup Required
echo ========================================
echo.
echo Before running the application, you need to:
echo.
echo 1. INSTALL TESSERACT OCR:
echo    - Download from: https://github.com/tesseract-ocr/tesseract/releases
echo    - Install the Windows installer
echo    - Default path: C:\Program Files\Tesseract-OCR\tesseract.exe
echo.
echo 2. GET API KEYS:
echo    - OpenAI: https://platform.openai.com/api-keys
echo    - Anthropic: https://console.anthropic.com/
echo.
echo 3. EDIT .env FILE:
echo    - Open .env file in notepad
echo    - Add your API keys
echo.
echo Would you like me to:
echo [1] Open the Tesseract download page
echo [2] Open .env file for editing
echo [3] Test the installation
echo [4] Run the application
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    start https://github.com/tesseract-ocr/tesseract/releases
    echo Tesseract download page opened in browser
    pause
    goto menu
)

if "%choice%"=="2" (
    notepad .env
    echo .env file opened for editing
    pause
    goto menu
)

if "%choice%"=="3" (
    echo Running component tests...
    python test_components.py
    pause
    goto menu
)

if "%choice%"=="4" (
    echo Starting AI Screen Reader...
    python main.py
    pause
    goto menu
)

if "%choice%"=="5" (
    exit /b 0
)

:menu
echo.
echo What would you like to do next?
echo [1] Open Tesseract download page
echo [2] Edit .env file
echo [3] Test installation
echo [4] Run application
echo [5] Exit
echo.
set /p choice="Enter your choice (1-5): "
goto menu
