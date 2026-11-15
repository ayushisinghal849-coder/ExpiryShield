@echo off
setlocal
cd /d "%~dp0"
echo ExpiryShield repair and startup
 echo This will try to install Python 3.12 using the Python install manager,
 echo then launch the main startup script.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found. Trying winget...
  where winget >nul 2>nul
  if errorlevel 1 (echo winget not found. Please install Python 3.12 x64 manually.& pause& exit /b 1)
  winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements
) else (
  py install 3.12
)
call "%~dp0START_EXPIRYAHEILD.bat"
