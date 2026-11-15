@echo off
 echo This will stop ExpiryShield servers running on ports 8000 and 5173.
 echo Closing the two server terminal windows is also sufficient.
 pause
 for %%P in (8000 5173) do (
   for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr LISTENING') do taskkill /PID %%A /T /F >nul 2>nul
 )
 echo ExpiryShield server processes stopped.
 pause
