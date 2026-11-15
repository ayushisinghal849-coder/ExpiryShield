EXPIRYSHIELD - WINDOWS STARTUP
==============================

1. Extract this ZIP completely to a normal folder. Do not run the BAT from
   inside the ZIP preview.
2. Install Python 3.12 (64-bit) and Node.js LTS (npm is included).
   Python: https://www.python.org/downloads/release/python-31210/
   Node.js: https://nodejs.org/
3. Open the extracted folder and double-click START_EXPIRYAHEILD.bat.
4. The first run needs internet access to install Python and npm packages.
   It can take several minutes. Do not close the setup window during install.
5. Two server windows should open. Keep both open while using the app.
6. The browser should open http://localhost:5173

WHAT CHANGED IN THIS BUILD
--------------------------
- Each sidebar workspace now has its own page and relevant data view.
- Five selectable sample scenarios are available from the top scenario picker.
- Loading a scenario replaces the active demo data, sales history and old actions.
- CSV import replaces the current demo dataset by default, so outputs are based
  on the uploaded file instead of being mixed with previous sample data.
- Include daily_sales_per_day in a CSV to provide 30 days of sample sales history.
- Five ready-to-upload CSV files are in data/sample and can be downloaded from
  the Import CSV dialog in the app.
- The action engine can produce TRANSFER, DISCOUNT, BUNDLE and FEFO outcomes.

DEMO WORKFLOW
-------------
1. Start the application.
2. Choose one of the five sample scenarios in the top dropdown.
3. Click Load sample.
4. Open Risk analysis and click Run risk analysis.
5. Review Inventory, Store matching and Recommendations pages.
6. Open Approvals to approve/reject/execute a recommendation.
7. Open Impact report to review estimated and completed impact.

Useful addresses:
  Frontend:  http://localhost:5173
  Backend:   http://localhost:8000
  API docs:  http://localhost:8000/docs

IF IT DOES NOT OPEN
-------------------
- Make sure the ZIP is extracted, not opened in File Explorer's ZIP preview.
- Open Command Prompt in this folder and run START_EXPIRYAHEILD.bat.
- Keep both backend and frontend terminal windows open.
- If package installation fails, check internet access and rerun the BAT.
- If the browser says it cannot connect, inspect both server windows.
