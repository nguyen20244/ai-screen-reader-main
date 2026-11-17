@echo off
echo ========================================
echo Tesseract OCR Download Helper
echo ========================================
echo.

echo Opening Tesseract download page...
echo.
echo Look for a file named like:
echo   tesseract-ocr-w64-setup-5.x.x.xxxxxxxx.exe
echo.
echo This will open the download page in your browser:

start https://digi.bib.uni-mannheim.de/tesseract/

echo.
echo ========================================
echo DOWNLOAD INSTRUCTIONS:
echo ========================================
echo.
echo 1. Download: tesseract-ocr-w64-setup-5.x.x.xxxxxxxx.exe
echo    (Choose the 64-bit version - w64)
echo.
echo 2. Run the downloaded .exe file
echo.
echo 3. Install to default location:
echo    C:\Program Files\Tesseract-OCR\
echo.
echo 4. After installation, run quick_start.bat
echo.
echo ========================================
echo.

echo Alternative download links:
echo.
echo If the main page doesn't work, try these:
echo 1. https://github.com/UB-Mannheim/tesseract/wiki
echo 2. https://tesseract-ocr.github.io/tessdoc/Downloads.html
echo.

pause
