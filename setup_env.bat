@echo off
REM Setup script: creates venv and installs requirements (run after Python is installed and in PATH)
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found in PATH. Please install Python 3.10+ and check "Add Python to PATH".
  echo Download: https://www.python.org/downloads/
  pause
  exit /b 1
)





















pauseecho    python core\main_controller.pyecho    call venv\Scripts\activate.batecho Setup complete. To run the assistant:)  exit /b 1  pause  echo pip install failed. Check the error messages above.pip install -r requirements.txt
nif errorlevel 1 (
necho Installing requirements...python -m pip install --upgrade pipcall venv\Scripts\activate.bat
necho Upgrading pip...
necho Activating venv...)  exit /b 1  pause  echo Failed to create venv. Ensure Python can create virtual environments.if errorlevel 1 (python -m venv venvnecho Creating virtual environment...