@echo off
setlocal

set "VENV_DIR=.venv"

echo [1/4] Creating virtual environment in %VENV_DIR%...
python -m venv %VENV_DIR%
if errorlevel 1 (
  echo Failed to create virtual environment.
  exit /b 1
)

echo [2/4] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo Failed to activate virtual environment.
  exit /b 1
)

echo [3/4] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo Failed to upgrade pip.
  exit /b 1
)

echo [4/4] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install dependencies.
  exit /b 1
)

echo.
echo Setup complete.
echo To activate later, run: .venv\Scripts\activate

endlocal
