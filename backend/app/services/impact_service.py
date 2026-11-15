from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.recommendation import Recommendation
from app.models.action import Action
from app.models.batch import Batch
from app.models.product import Product
from app.models.store import Store

def calculate_impact_metrics(db: Session) -> dict:
    """
    Computes overall inventory recovery and financial impact metrics.
    Tracks approved and completed transfers and recommendations.
    """
    completed_actions = (
        db.query(Action)
        .filter(Action.execution_status == "COMPLETED")
        .all()
    )

    total_transferred_units = 0
    total_revenue_protected = 0.0
    total_net_value_protected = 0.0
    successful_transfers_count = 0
    store_impact = {}

    for action in completed_actions:
        rec = db.query(Recommendation).filter(Recommendation.id == action.recommendation_id).first()
        if not rec:
            continue

        total_transferred_units += rec.recommended_quantity
        total_revenue_protected += rec.expected_value
        net_val = rec.expected_value - rec.estimated_cost
        total_net_value_protected += net_val

        if rec.action_type == "TRANSFER":
            successful_transfers_count += 1

        # Track store wise impact
        src_store = db.query(Store).filter(Store.id == rec.source_store_id).first()
        src_name = src_store.store_name if src_store else f"Store {rec.source_store_id}"
        
        if src_name not in store_impact:
            store_impact[src_name] = {
                "units_saved": 0,
                "value_protected": 0.0,
                "transfers_executed": 0
            }
        store_impact[src_name]["units_saved"] += rec.recommended_quantity
        store_impact[src_name]["value_protected"] += round(net_val, 2)
        if rec.action_type == "TRANSFER":
            store_impact[src_name]["transfers_executed"] += 1

    # Approximate CO2 waste reduction estimate: ~2.5 kg CO2e saved per kg food/inventory saved
    estimated_co2_kg_saved = round(total_transferred_units * 0.8 * 2.5, 1)

    return {
        "total_units_transferred": total_transferred_units,
        "total_risky_inventory_recovered": total_transferred_units,
        "estimated_revenue_protected": round(total_revenue_protected, 2),
        "estimated_net_value_protected": round(total_net_value_protected, 2),
        "successful_transfers_count": successful_transfers_count,
        "estimated_co2_kg_saved": estimated_co2_kg_saved,
        "store_impact": store_impact
    }
