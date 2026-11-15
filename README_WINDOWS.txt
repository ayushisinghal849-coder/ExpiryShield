# ExpiryShield - Windows One-Click Prototype

## Start
1. Extract the entire ZIP using Windows **Extract All**. Do not run files inside the ZIP preview.
2. Install Node.js LTS from https://nodejs.org/ if it is not installed.
3. Double-click `START_EXPIRYAHEILD.bat`.
4. The launcher prefers Python 3.12 64-bit. If it is missing, it attempts installation using `winget`. If winget is unavailable, install Python 3.12 64-bit manually and run the BAT again.
5. The launcher creates `backend\.venv`, updates pip, installs Python packages using binary wheels where available, installs frontend packages, then starts both servers.

## URLs
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Troubleshooting
- Run `DIAGNOSE_EXPIRYAHEILD.bat` and share its output if setup fails.
- If package installation is interrupted, keep internet connected and run `START_EXPIRYAHEILD.bat` again. It reuses the virtual environment.
- Keep the two server terminal windows open while using the app.
- Use `STOP_EXPIRYAHEILD.bat` to stop local services if supplied.

The requirements use compatible version ranges so pip can choose prebuilt wheels for Python 3.12 on Windows. This avoids the earlier attempt to build the old pinned Pandas release from source.

PYTHON 3.12 INSTALL NOTE
If the startup window says "No runtime installed that matches 3.12", this
package now tries `py install 3.12` first and then winget. Keep an internet
connection available. If automatic installation is blocked by Windows policy,
install Python 3.12 64-bit manually from python.org, enable the Python Launcher,
and rerun START_EXPIRYAHEILD.bat.
