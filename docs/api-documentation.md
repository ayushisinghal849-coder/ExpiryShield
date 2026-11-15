# ExpiryShield REST API Specification

Base URL: `http://127.0.0.1:8000`
Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`

---

## Endpoints Summary

### System & Health
- `GET /health` : Verify system uptime and API readiness.
- `GET /` : API Welcome and documentation pointers.

### Inventory & Batches
- `GET /inventory` : List all batches with real-time risk scores and store details. Filterable by `store_id`, `category`, `risk_level`, `search`.
- `POST /inventory` : Register a new batch with batch code, store, quantity, and expiry date.
- `PUT /inventory/{id}` : Update batch quantity or adjust expiry date.
- `GET /products` : List master product catalogue.
- `POST /products` : Create new product SKU with selling price and cost price.
- `POST /inventory/upload-csv` : Multipart CSV file upload with validation and error reporting.

### Stores
- `GET /stores` : List all retail stores with GPS coordinates.
- `POST /stores` : Register a new retail store.

### Expiry Risk Analysis
- `POST /analyze` : Run expiry risk engine over inventory. Computes daily demand, expected consumption, surplus units, and 0-100 risk score.

### Recommendations & Strategy Ranking
- `GET /recommend` : Returns ranked recommendations comparing Transfer, Discount, Bundle, FEFO, and Procure Less.
- `GET /recommendations/{id}` : Detailed information on a specific recommendation.

### Approvals & Atomic Execution
- `GET /approvals` : List all pending, approved, and completed recommendations.
- `POST /approve` : Approve a pending recommendation. Validates stock availability.
- `POST /reject` : Reject an action recommendation.
- `POST /complete` : Atomically executes an approved transfer (decrements source stock, increments destination stock, records completed action). Prevents duplicate and unapproved execution.

### Impact Analytics & Demo Utilities
- `GET /analytics` : Returns aggregate dashboard metrics, store comparisons, and realized recovery impact.
- `POST /reset-demo-data` : Restores database to initial pristine baseline hackathon dataset.
