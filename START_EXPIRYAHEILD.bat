@echo off
setlocal EnableExtensions
chcp 65001 >nul
title ExpiryShield - One Click Startup
color 0B
set "ROOT=%~dp0"
cd /d "%ROOT%"
echo.
echo ==========================================================
echo             EXPIRYSHIELD - ONE CLICK STARTUP
echo ==========================================================
echo Project: "%ROOT%"
echo.
if not exist "%ROOT%backend\requirements.txt" (echo [ERROR] backend\requirements.txt not found.& goto :fail)
if not exist "%ROOT%frontend\package.json" (echo [ERROR] frontend\package.json not found.& goto :fail)

REM --- Find a 64-bit Python 3.12 runtime; install it if missing ---
set "PYLAUNCH="
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -c "import struct,sys; sys.exit(0 if struct.calcsize('P')*8==64 else 1)" >nul 2>nul
  if not errorlevel 1 set "PYLAUNCH=py -3.12"
)
if not defined PYLAUNCH (
  echo [INFO] Python 3.12 was not found. Trying the Python install manager...
  where py >nul 2>nul
  if not errorlevel 1 (
    py install 3.12
    py -3.12 -c "import struct,sys; sys.exit(0 if struct.calcsize('P')*8==64 else 1)" >nul 2>nul
    if not errorlevel 1 set "PYLAUNCH=py -3.12"
  )
)
if not defined PYLAUNCH (
  echo [INFO] Trying Windows Package Manager (winget) to install Python 3.12...
  where winget >nul 2>nul
  if not errorlevel 1 (
    winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
    if not errorlevel 1 (
      py -3.12 -c "import struct,sys; sys.exit(0 if struct.calcsize('P')*8==64 else 1)" >nul 2>nul
      if not errorlevel 1 set "PYLAUNCH=py -3.12"
    )
  )
)
if not defined PYLAUNCH (
  echo.
  echo [ERROR] Python 3.12 x64 could not be installed automatically.
  echo Please install Python 3.12 x64 from https://www.python.org/downloads/release/python-31210/
  echo During setup, enable the Python Launcher option. Then run this BAT again.
  goto :fail
)

echo [1/5] Python selected:
%PYLAUNCH% --version
%PYLAUNCH% -c "import struct; print('Architecture:',struct.calcsize('P')*8,'bit')"

REM --- Check Node.js and npm ---
echo.
echo [2/5] Checking Node.js and npm...
where node >nul 2>nul
if errorlevel 1 (echo [ERROR] Node.js is missing. Install Node.js LTS from https://nodejs.org/ & goto :fail)
where npm.cmd >nul 2>nul
if errorlevel 1 (echo [ERROR] npm is missing. Reinstall Node.js LTS with npm included. & goto :fail)
node --version
call npm.cmd --version
if errorlevel 1 (echo [ERROR] npm could not run. Reinstall Node.js LTS.& goto :fail)

REM --- Create Python environment ---
echo.
echo [3/5] Preparing backend virtual environment...
if not exist "%ROOT%backend\.venv\Scripts\python.exe" (
  %PYLAUNCH% -m venv "%ROOT%backend\.venv"
  if errorlevel 1 (echo [ERROR] Could not create Python virtual environment.& goto :fail)
)
set "VENV_PY=%ROOT%backend\.venv\Scripts\python.exe"

REM --- Install Python dependencies using wheels; no Visual Studio build required ---
echo.
echo [4/5] Installing backend dependencies...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (echo [ERROR] pip upgrade failed. Check internet connection.& goto :fail)
"%VENV_PY%" -m pip install --prefer-binary -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Backend dependency installation failed.
  echo Check internet access and rerun this file. Python 3.12 x64 is selected for wheel support.
  goto :fail
)

REM --- Install frontend dependencies ---
echo.
echo [5/5] Installing frontend dependencies...
if not exist "%ROOT%frontend\node_modules\vite\bin\vite.js" (
  pushd "%ROOT%frontend"
  call npm.cmd install --no-audit --no-fund
  if errorlevel 1 (popd & echo [ERROR] npm install failed. Check internet connection.& goto :fail)
  popd
)

echo.
echo Starting backend and frontend in separate windows...
start "ExpiryShield Backend" cmd /k "cd /d ""%ROOT%backend"" ^&^& ""%VENV_PY%"" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "ExpiryShield Frontend" cmd /k "cd /d ""%ROOT%frontend"" ^&^& call npm.cmd run dev -- --host 127.0.0.1 --port 5173"
echo.
echo Waiting 12 seconds for servers to start...
timeout /t 12 /nobreak >nul
start "" "http://localhost:5173"
echo.
echo ==========================================================
echo Startup commands have been launched.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Keep both server windows open while using ExpiryShield.
echo To stop, close the two server windows.
echo ==========================================================
echo.
pause
exit /b 0

:fail
echo.
echo Startup stopped. The error is shown above.
echo Run DIAGNOSE_EXPIRYAHEILD.bat and share its output if needed.
echo.
pause
exit /b 1
