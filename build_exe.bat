@echo off
REM ============================================================
REM Build AI Desktop Assistant as a standalone EXE
REM ============================================================
REM Prerequisites:
REM   - Python 3.10+ with pip
REM   - PyInstaller: pip install pyinstaller
REM ============================================================

echo.
echo ========================================
echo   AI Desktop Assistant - Build Script
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [!] No virtual environment found, using system Python
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Create dist folder
if not exist dist mkdir dist
if not exist build mkdir build

echo.
echo [*] Building executable...
echo.

REM Build the executable
pyinstaller ^
    --onefile ^
    --windowed ^
    --name AIDesktopAssistant ^
    --add-data ".env.example;." ^
    --add-data "README.md;." ^
    --add-data "SAFETY.md;." ^
    --hidden-import=pyttsx3.drivers ^
    --hidden-import=pyttsx3.drivers.sapi5 ^
    --hidden-import=sounddevice ^
    --hidden-import=numpy ^
    main.py

if errorlevel 1 (
    echo.
    echo [X] Build FAILED!
    echo     Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD SUCCESSFUL!
echo ========================================
echo.
echo   Executable: dist\AIDesktopAssistant.exe
echo.
echo   IMPORTANT:
echo   - Copy .env.example to .env and configure before running
echo   - Install Ollama separately: https://ollama.ai
echo   - GPU (CUDA) recommended for best performance
echo.
echo   To run:
echo   1. Navigate to dist folder
echo   2. Run AIDesktopAssistant.exe
echo.
pause
