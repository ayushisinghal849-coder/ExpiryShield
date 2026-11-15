@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ===== ExpiryShield diagnostics =====
echo Project: %CD%
echo.
echo -- Python launcher --
where py 2>nul
if not errorlevel 1 py -0p
echo.
echo -- Python commands --
where python 2>nul
python --version 2>&1
python -c "import struct; print(str(struct.calcsize('P')*8)+'-bit')" 2>&1
echo.
echo -- Node and npm --
where node 2>nul
node --version 2>&1
where npm 2>nul
call npm.cmd --version 2>&1
echo.
echo -- Required project paths --
if exist backend\requirements.txt (echo backend requirements: FOUND) else (echo backend requirements: MISSING)
if exist frontend\package.json (echo frontend package: FOUND) else (echo frontend package: MISSING)
echo.
pause
