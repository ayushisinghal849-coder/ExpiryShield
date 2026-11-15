from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date

from app.models.product import Product
from app.models.batch import Batch
from app.models.store import Store
from app.services.distance_service import calculate_haversine_distance, calculate_transport_cost
from app.services.demand_service import calculate_average_daily_demand
from app.services.risk_engine import evaluate_batch_risk
from app.services.matching_engine import find_cross_store_matches

def rank_and_generate_recommendations(db: Session) -> List[Dict[str, Any]]:
    """
    Evaluates batches facing expiry risks and generates ranked recommendations comparing:
    1. TRANSFER: Move surplus stock to nearby store with demand shortage.
    2. DISCOUNT: Apply 20%-40% markdown to accelerate in-store sales velocity.
    3. BUNDLE: Offer 2-for-1 or package bundle to clear stock fast.
    4. FEFO: Ensure shelf rotation prioritizing early expiring batch.
    5. PROCURE LESS: Flag oversupply to purchasing for upcoming orders.
    """
    recommendations = []
    
    # 1. Check all cross-store transfer matches first
    transfer_matches = find_cross_store_matches(db)

    # Track batches already addressed by transfer
    matched_batch_ids = set()

    for match in transfer_matches:
        batch = match["batch"]
        product = match["product"]
        src_store = match["source_store"]
        dest_store = match["destination_store"]
        qty = match["transfer_quantity"]
        val = match["expected_value"]
        cost = match["transport_cost"]
        net = match["net_benefit"]

        # Build alternative actions for comparison
        alternatives = [
            {
                "action_type": "DISCOUNT",
                "expected_value": round(qty * product.selling_price * 0.7, 2), # 30% discount
                "estimated_cost": round(qty * product.selling_price * 0.3, 2),
                "net_benefit": round(qty * product.selling_price * 0.7, 2),
                "feasibility": "Medium",
                "description": f"Apply 30% discount in {src_store.store_name} to boost local sales velocity."
            },
            {
                "action_type": "BUNDLE",
                "expected_value": round(qty * product.selling_price * 0.6, 2),
                "estimated_cost": round(qty * product.selling_price * 0.4, 2),
                "net_benefit": round(qty * product.selling_price * 0.6, 2),
                "feasibility": "High",
                "description": "Bundle with complementary product to liquidate remaining units."
            },
            {
                "action_type": "FEFO",
                "expected_value": round(qty * product.selling_price * 0.3, 2),
                "estimated_cost": 0.0,
                "net_benefit": round(qty * product.selling_price * 0.3, 2),
                "feasibility": "High",
                "description": "Reposition batch to front-of-shelf (FEFO), though surplus will still remain."
            },
            {
                "action_type": "PROCURE_LESS",
                "expected_value": round(qty * product.cost_price, 2),
                "estimated_cost": 0.0,
                "net_benefit": round(qty * product.cost_price, 2),
                "feasibility": "High",
                "description": "Reduce next replenishment purchase order to prevent future surplus."
            }
        ]

        rec = {
            "source_store_id": src_store.id,
            "source_store_name": src_store.store_name,
            "destination_store_id": dest_store.id,
            "destination_store_name": dest_store.store_name,
            "product_id": product.id,
            "product_name": product.product_name,
            "batch_id": batch.id,
            "batch_code": batch.batch_code,
            "recommended_quantity": qty,
            "action_type": "TRANSFER",
            "expected_value": val,
            "estimated_cost": cost,
            "net_benefit": net,
            "distance_km": match["distance_km"],
            "risk_score": match["risk_score"],
            "reason": match["explanation"],
            "ranking": 1,
            "alternatives": alternatives
        }
        recommendations.append(rec)
        matched_batch_ids.add(batch.id)

    # 2. For other risky batches not transferred (e.g. no destination store shortage, or short shelf life)
    risky_batches = db.query(Batch).filter(Batch.quantity > 0).all()
    for batch in risky_batches:
        if batch.id in matched_batch_ids:
            continue

        product = db.query(Product).filter(Product.id == batch.product_id).first()
        store = db.query(Store).filter(Store.id == batch.store_id).first()
        if not product or not store:
            continue

        daily_demand = calculate_average_daily_demand(db, product.id, store.id)
        risk_info = evaluate_batch_risk(batch.quantity, batch.expiry_date, daily_demand)

        if risk_info["surplus_quantity"] > 0 and risk_info["risk_level"] in ["HIGH", "MEDIUM"]:
            qty = risk_info["surplus_quantity"]
            days_left = risk_info["days_to_expiry"]

            surplus_ratio = qty / max(batch.quantity, 1)
            # Select a different action according to urgency and the size of the surplus.
            if days_left <= 4:
                action_type = "DISCOUNT"
                discount_rate = 0.35
                exp_val = round(qty * product.selling_price * (1 - discount_rate), 2)
                est_cost = round(qty * product.selling_price * discount_rate, 2)
                reason = f"Only {days_left} days remain and {qty} units are at risk. A 35% markdown is the fastest practical sell-through action."
            elif days_left <= 7 and surplus_ratio >= 0.60:
                action_type = "BUNDLE"
                exp_val = round(qty * product.selling_price * 0.80, 2)
                est_cost = round(qty * product.selling_price * 0.15, 2)
                reason = f"{qty} surplus units ({surplus_ratio:.0%} of this batch) have {days_left} days remaining. A bundle promotion can accelerate sell-through while preserving more value than a deep markdown."
            else:
                action_type = "FEFO"
                exp_val = round(qty * product.selling_price * 0.8, 2)
                est_cost = 50.0
                reason = f"Prioritize this batch at the front of the shelf using FEFO in {store.store_name}; no economical cross-store shortage match was found."

            alternatives = [
                {
                    "action_type": "DISCOUNT",
                    "expected_value": round(qty * product.selling_price * 0.7, 2),
                    "estimated_cost": round(qty * product.selling_price * 0.3, 2),
                    "net_benefit": round(qty * product.selling_price * 0.7, 2),
                    "feasibility": "High",
                    "description": "Flash markdown discount."
                },
                {
                    "action_type": "BUNDLE",
                    "expected_value": round(qty * product.selling_price * 0.5, 2),
                    "estimated_cost": round(qty * product.selling_price * 0.5, 2),
                    "net_benefit": round(qty * product.selling_price * 0.5, 2),
                    "feasibility": "Medium",
                    "description": "Bundle with high-turnover grocery essentials."
                },
                {
                    "action_type": "PROCURE_LESS",
                    "expected_value": round(qty * product.cost_price, 2),
                    "estimated_cost": 0.0,
                    "net_benefit": round(qty * product.cost_price, 2),
                    "feasibility": "High",
                    "description": "Notify supply chain to curb reorder volume."
                }
            ]

            recommendations.append({
                "source_store_id": store.id,
                "source_store_name": store.store_name,
                "destination_store_id": None,
                "destination_store_name": None,
                "product_id": product.id,
                "product_name": product.product_name,
                "batch_id": batch.id,
                "batch_code": batch.batch_code,
                "recommended_quantity": qty,
                "action_type": action_type,
                "expected_value": exp_val,
                "estimated_cost": est_cost,
                "net_benefit": round(exp_val - est_cost, 2),
                "distance_km": 0.0,
                "risk_score": risk_info["risk_score"],
                "reason": reason,
                "ranking": 2 if action_type == "DISCOUNT" else 3,
                "alternatives": alternatives
            })

    # Sort recommendations by net_benefit descending & risk_score descending
    recommendations.sort(key=lambda r: (r["net_benefit"], r["risk_score"]), reverse=True)
    for idx, r in enumerate(recommendations):
        r["ranking"] = idx + 1

    return recommendations
