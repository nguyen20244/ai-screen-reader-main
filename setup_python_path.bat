@echo off
echo ========================================
echo Adding Python to PATH and Starting App
echo ========================================
echo.

REM Set Python path for this session
set PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313
set PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%

echo ✅ Python path added for this session
echo Python location: %PYTHON_PATH%
echo.

echo Testing Python...
python --version
if errorlevel 1 (
    echo ❌ Python still not accessible
    pause
    exit /b 1
)

echo ✅ Python is now working!
echo.

echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install pillow pytesseract pyautogui opencv-python numpy openai anthropic python-dotenv

if errorlevel 1 (
    echo ❌ Failed to install some packages
    echo Continuing anyway...
)

echo.
echo ✅ Packages installed!
echo.

echo Testing components...
python test_components.py

echo.
echo ========================================
echo Starting AI Screen Reader...
echo ========================================
echo.

python main.py

echo.
echo Application closed.
pause
