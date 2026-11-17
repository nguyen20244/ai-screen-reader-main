@echo off
echo ========================================
echo Testing Python Installation
echo ========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python first:
    echo 1. Microsoft Store: Install Python 3.11
    echo 2. Or python.org: Download and install with "Add to PATH" checked
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Python is working!
echo.

echo Checking pip...
python -m pip --version
if errorlevel 1 (
    echo ❌ pip is not available
    pause
    exit /b 1
)

echo ✅ pip is working!
echo.

echo Python installation is ready!
echo You can now run the AI Screen Reader.
echo.
pause
