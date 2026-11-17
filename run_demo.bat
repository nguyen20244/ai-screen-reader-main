@echo off
echo ========================================
echo AI Screen Reader - DEMO MODE
echo ========================================
echo.
echo IMPORTANT INFORMATION:
echo.
echo 1. OpenAI API Keys are NOT FREE
echo    - Your key has exceeded its quota
echo    - You need to add payment method at: https://platform.openai.com/billing
echo.
echo 2. Tesseract OCR Status:
echo    - You have Tesseract installed (v5.5.0)
echo    - The app will find it automatically
echo.
echo 3. Demo Mode Features:
echo    - Full screen capture and OCR
echo    - Question detection works perfectly
echo    - Sample AI answers (not real AI)
echo    - All GUI features functional
echo.
echo Starting in DEMO MODE...
echo Press Ctrl+C to exit
echo.

REM Set Python path and start demo
set PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313
set PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%

python start_with_demo.py

echo.
echo Demo session ended.
pause
