@echo off
echo ========================================
echo Installing Ollama - Free Local AI
echo ========================================
echo.

echo Ollama is a free, local AI that runs on your computer:
echo - No API keys needed
echo - No internet required after setup
echo - Completely free
echo - Privacy-focused (everything runs locally)
echo.

echo Opening Ollama download page...
start https://ollama.ai/download

echo.
echo INSTALLATION STEPS:
echo ========================================
echo.
echo 1. Download Ollama from the website that just opened
echo 2. Install Ollama (follow the installer)
echo 3. Open Command Prompt or PowerShell
echo 4. Run: ollama pull llama3.2:1b
echo    (This downloads a lightweight AI model - about 1GB)
echo 5. Run: ollama serve
echo    (This starts the Ollama server)
echo.
echo After installation, run: start_with_ollama.bat
echo.

echo Alternative models you can try:
echo - ollama pull llama3.2:3b    (Better quality, 2GB)
echo - ollama pull mistral:7b     (Even better, 4GB)
echo - ollama pull codellama:7b   (Good for coding questions)
echo.

echo ========================================
echo Benefits of Ollama:
echo ========================================
echo + Completely FREE
echo + No API limits
echo + Works offline
echo + Private (no data sent to servers)
echo + Multiple AI models available
echo + Fast responses
echo.

pause
