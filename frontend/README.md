# ExpiryShield Frontend

## Run locally
```bash
npm install
cp .env.example .env
npm run dev
```
The frontend runs at http://localhost:5173 and expects the FastAPI backend at http://localhost:8000.

## Dashboard integration
The dashboard calls the existing backend endpoints:
- `GET /analytics`
- `GET /inventory`
- `GET /stores`
- `GET /recommend`
- `POST /analyze`
- `POST /approve`
- `POST /reject`
- `POST /complete`
- `POST /inventory/upload-csv`

If the API is not running, the UI displays clearly labelled preview data so the dashboard can still be explored.
