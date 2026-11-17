@echo off
echo ========================================
echo AI Screen Reader with Ollama (FREE AI)
echo ========================================
echo.

REM Check if Ollama is installed
ollama --version >nul 2>&1
if errorlevel 1 (
    echo Ollama is not installed or not in PATH
    echo.
    echo Please install Ollama first:
    echo 1. Run: install_ollama.bat
    echo 2. Follow the installation instructions
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✓ Ollama is installed
echo.

echo Checking if Ollama server is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    start /B ollama serve
    echo Waiting for server to start...
    timeout /t 5 /nobreak >nul
) else (
    echo ✓ Ollama server is already running
)

echo.
echo Checking for AI models...
ollama list | findstr llama3.2 >nul
if errorlevel 1 (
    echo Downloading lightweight AI model (llama3.2:1b - about 1GB)...
    echo This may take a few minutes...
    ollama pull llama3.2:1b
    if errorlevel 1 (
        echo Failed to download model. Check your internet connection.
        pause
        exit /b 1
    )
) else (
    echo ✓ AI model is available
)

echo.
echo ========================================
echo Starting AI Screen Reader with FREE AI
echo ========================================
echo.

REM Set Python path and start app
set PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313
set PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%

python free_ai_app.py

echo.
echo Session ended.
pause
