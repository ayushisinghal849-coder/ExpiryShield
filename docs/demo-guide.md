# ExpiryShield Hackathon Demonstration Guide (3–5 Minutes)

This walkthrough guides you through demonstrating the full end-to-end capabilities of ExpiryShield to software judges.

---

## 1. Context & The Retail Dilemma (0:00 - 0:45)
- **The Problem**: Retail grocery and FMCG stores lose hundreds of thousands in margins each quarter because inventory expires on store shelves while nearby sibling stores within 10 km are running out of stock for the very same items.
- **The Solution**: **ExpiryShield** is an automated multi-store inventory balancing and expiry-risk engine that detects surplus, calculates distance via Haversine, and recommends the highest ROI action before write-offs occur.

---

## 2. Dashboard & Inventory Overview (0:45 - 1:30)
1. Navigate to **Dashboard** (`http://localhost:3000` or `http://localhost:5173`).
2. Show the **Expiry Horizon** chart and **Store Comparison** chart showing surplus stock at risk across Bengaluru stores.
3. Open **Inventory**:
   - Filter by **High Risk** to highlight batches nearing expiration.
   - Show the **Store Filter** dropdown in the header to focus on Store A (Indiranagar).

---

## 3. The Core Primary Hackathon Demo Scenario (1:30 - 3:00)
1. Navigate to **Expiry Analysis**:
   - Click the **"Run Expiry Analysis"** button.
   - Highlight **Milk Powder (500g)** in Store A:
     - **Current Stock**: 100 units
     - **Sales Velocity**: 3 units/day (based on historical sales)
     - **Days to Expiry**: 7 days
     - **Expected Consumption**: $3 \times 7 = 21$ units
     - **Surplus at Risk**: $100 - 21 = \mathbf{79}$ units at risk of expiration.
2. Navigate to **Store Matching**:
   - Show the automated pairing card:
     - **Source**: Store A (79 units surplus)
     - **Destination**: Store B (Koramangala, selling 12 units/day with only 20 units in stock -> demand gap of **64 units** over 7 days).
     - **Transfer Quantity**: $\min(79, 64) = \mathbf{64}$ units.
     - **Distance**: Calculated via Haversine formula as **8.0 km**.
     - **Gross Value**: $64 \times ₹200 = \mathbf{₹12,800}$.
     - **Transit Cost**: Base ₹200 + $8 \times ₹25 = \mathbf{₹400}$.
     - **Net Recovery Benefit**: $₹12,800 - ₹400 = \mathbf{₹12,400}$.
3. Navigate to **Recommendations**:
   - Show the **Strategy Comparison matrix** proving why Transfer is ranked #1 over a 30% Markdown Discount (which would only recover ₹8,960) or FEFO shelf rotation.

---

## 4. Approval & Atomic Execution (3:00 - 4:15)
1. On the Milk Powder card, click **"Approve Action"**.
   - Notice the status updates to **APPROVED** with a toast notification.
2. Click **"Execute & Complete Transfer"**:
   - The transaction commits immediately in SQLite.
3. Check the immediate verification:
   - Go to **Inventory**: Store A's Milk Powder stock has decreased from 100 units to **36 units** ($100 - 64$).
   - Store B now has received **84 units** ($20 + 64$).
   - Trying to complete again correctly blocks duplicate execution.

---

## 5. Realized Impact Analytics (4:15 - 5:00)
1. Go to **Impact Analytics**:
   - **Units Rebalanced**: 64 units
   - **Gross Value Protected**: ₹12,800
   - **Net Value Saved**: ₹12,400
   - **CO2 Avoidance**: ~128 kg CO2e
2. Go to **Settings**:
   - Demonstrate the **"Reset Demo Database to Baseline"** button, which wipes and restores the initial pristine demo scenario in 1 second for consecutive judge demonstrations.
