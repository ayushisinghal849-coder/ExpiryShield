# ExpiryShield System Architecture

ExpiryShield is designed with a clean, decoupled 3-tier architecture:

```
[ React + Vite Client (Port 3000/5173) ]
                   │
         REST API (Axios JSON)
                   │
                   ▼
       [ FastAPI Gateway (Port 8000) ]
        ├── Routers (Inventory, Stores, Analysis, Recommendations, Approvals, Analytics)
        ├── Business Engines:
        │     ├── Demand Forecasting (Pandas historical sales velocity)
        │     ├── Expiry Risk Engine (Shelf-life & surplus scoring 0-100)
        │     ├── Haversine Distance Engine (Inter-store coordinate geodesic)
        │     ├── Cross-Store Matching Engine (Surplus-to-Shortage pairing)
        │     ├── Action Ranking Engine (ROI comparison: Transfer vs Discount vs FEFO vs Bundle)
        │     └── Impact & Recovery Service (Protected value & waste avoidance)
        └── SQLite Database Layer (SQLAlchemy ORM + Atomic Transactions)
```

## Data Schema & Entities

- **Store**: Multi-outlet physical metadata including latitude and longitude.
- **Product**: Master SKU catalogue, cost price, and retail selling price.
- **Batch**: Discrete inventory instances mapped to a store, quantity, and expiration date.
- **Sale**: Daily historical sales ledger used for demand forecasting.
- **Recommendation**: Ranked intervention candidates with financial valuations and justifications.
- **Action**: State tracking ledger for approval and execution verification.

## Core Formulations

1. **Haversine Distance Formula**:
   $$\Delta \phi = \text{lat}_2 - \text{lat}_1, \quad \Delta \lambda = \text{lon}_2 - \text{lon}_1$$
   $$a = \sin^2(\Delta \phi / 2) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2(\Delta \lambda / 2)$$
   $$d = 2 R \cdot \text{atan2}(\sqrt{a}, \sqrt{1 - a})$$

2. **Average Daily Demand (Sales Velocity)**:
   $$\text{Daily Demand} = \frac{\sum \text{Historical Units Sold}}{\text{Days in Lookback Period}}$$

3. **Expected Consumption**:
   $$\text{Expected Consumption} = \text{Daily Demand} \times \text{Days Until Expiry}$$

4. **Surplus at Risk**:
   $$\text{Surplus} = \max(0, \text{Stock Quantity} - \lfloor\text{Expected Consumption}\rfloor)$$

5. **Transfer Quantity**:
   $$\text{Transfer Qty} = \min(\text{Source Surplus}, \text{Destination Demand Gap})$$
