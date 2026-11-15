from typing import List, Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models.store import Store
from app.models.batch import Batch
from app.models.product import Product
from app.services.demand_service import calculate_average_daily_demand
from app.services.risk_engine import evaluate_batch_risk
from app.services.distance_service import calculate_haversine_distance, calculate_transport_cost

def find_cross_store_matches(
    db: Session,
    max_distance_km: float = 50.0,
    min_shelf_life_days: int = 4
) -> List[Dict[str, Any]]:
    """
    Finds cross-store transfer opportunities:
    1. Identifies source stores with batches having surplus inventory and sufficient shelf life (> min_shelf_life_days).
    2. Identifies destination stores with identical products experiencing demand shortages.
    3. Calculates Transfer Quantity = MIN(Source Surplus, Destination Demand Gap).
    4. Computes Haversine distance and transport costs.
    """
    matches = []
    stores = db.query(Store).all()
    stores_by_id = {s.id: s for s in stores}
    products = db.query(Product).all()

    for product in products:
        # Evaluate each store's state for this product
        store_surpluses = []
        store_shortages = []

        for store in stores:
            # Get batches in this store for this product
            batches = (
                db.query(Batch)
                .filter(Batch.product_id == product.id, Batch.store_id == store.id, Batch.quantity > 0)
                .all()
            )

            daily_demand = calculate_average_daily_demand(db, product.id, store.id)

            total_stock = sum(b.quantity for b in batches)

            for b in batches:
                risk_info = evaluate_batch_risk(b.quantity, b.expiry_date, daily_demand)
                days_left = risk_info["days_to_expiry"]

                # Only consider batches with remaining shelf life buffer for transfers
                if days_left >= min_shelf_life_days and risk_info["surplus_quantity"] > 0:
                    store_surpluses.append({
                        "store": store,
                        "batch": b,
                        "surplus": risk_info["surplus_quantity"],
                        "days_left": days_left,
                        "risk_score": risk_info["risk_score"],
                        "daily_demand": daily_demand
                    })

            # Check if this store has a shortage / demand gap over horizon
            # Typical planning horizon based on product shelf life (e.g. 7 days)
            horizon = 7
            expected_demand_over_horizon = daily_demand * horizon
            if expected_demand_over_horizon > total_stock:
                gap = int(expected_demand_over_horizon - total_stock)
                if gap > 0:
                    store_shortages.append({
                        "store": store,
                        "demand_gap": gap,
                        "daily_demand": daily_demand,
                        "current_stock": total_stock
                    })

        # Match surpluses with shortages across different stores
        for src in store_surpluses:
            for dest in store_shortages:
                if src["store"].id == dest["store"].id:
                    continue # Source and destination must be different

                distance = calculate_haversine_distance(
                    src["store"].latitude, src["store"].longitude,
                    dest["store"].latitude, dest["store"].longitude
                )

                if distance > max_distance_km:
                    continue # Too far for viable local transfer

                transfer_qty = min(src["surplus"], dest["demand_gap"])
                if transfer_qty <= 0:
                    continue

                transport_cost = calculate_transport_cost(distance)
                expected_value = round(transfer_qty * product.selling_price, 2)
                net_benefit = round(expected_value - transport_cost, 2)

                explanation = (
                    f"Transfer {transfer_qty} units of '{product.product_name}' from {src['store'].store_name} "
                    f"(Surplus: {src['surplus']}, daily demand {src['daily_demand']}) to {dest['store'].store_name} "
                    f"(Demand gap: {dest['demand_gap']}, daily demand {dest['daily_demand']}) across {distance} km."
                )

                matches.append({
                    "product": product,
                    "batch": src["batch"],
                    "source_store": src["store"],
                    "destination_store": dest["store"],
                    "transfer_quantity": transfer_qty,
                    "distance_km": distance,
                    "transport_cost": transport_cost,
                    "expected_value": expected_value,
                    "net_benefit": net_benefit,
                    "risk_score": src["risk_score"],
                    "explanation": explanation
                })

    return matches
