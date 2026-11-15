from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.store import Store
from app.models.product import Product
from app.models.batch import Batch
from app.models.recommendation import Recommendation
from app.models.action import Action
from app.services.impact_service import calculate_impact_metrics
from app.services.demand_service import calculate_average_daily_demand
from app.services.risk_engine import evaluate_batch_risk
from app.seed.demo_data import seed_database

router = APIRouter(prefix="", tags=["Analytics & Dashboard"])

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Returns dashboard overview, inventory statistics, risk breakdowns, 
    and realized impact from completed actions.
    """
    # 1. Total counts
    total_stores = db.query(Store).count()
    total_products = db.query(Product).count()
    
    batches = db.query(Batch).filter(Batch.quantity > 0).all()
    total_units = sum(b.quantity for b in batches)

    # 2. Risk breakdown
    high_risk_batches = 0
    med_risk_batches = 0
    low_risk_batches = 0
    surplus_units = 0

    for b in batches:
        daily_demand = calculate_average_daily_demand(db, b.product_id, b.store_id)
        risk = evaluate_batch_risk(b.quantity, b.expiry_date, daily_demand)
        surplus_units += risk["surplus_quantity"]
        if risk["risk_level"] in ["HIGH", "EXPIRED"]:
            high_risk_batches += 1
        elif risk["risk_level"] == "MEDIUM":
            med_risk_batches += 1
        else:
            low_risk_batches += 1

    # 3. Recommendations & Approvals counts
    pending_recs = db.query(Recommendation).filter(Recommendation.status == "PENDING").count()
    approved_recs = db.query(Recommendation).filter(Recommendation.status == "APPROVED").count()
    completed_recs = db.query(Recommendation).filter(Recommendation.status == "COMPLETED").count()

    # 4. Realized Impact Metrics
    impact = calculate_impact_metrics(db)

    # 5. Store comparison chart data
    stores = db.query(Store).all()
    store_comparison = []
    for s in stores:
        s_batches = db.query(Batch).filter(Batch.store_id == s.id, Batch.quantity > 0).all()
        s_units = sum(b.quantity for b in s_batches)
        s_surplus = 0
        for b in s_batches:
            daily_demand = calculate_average_daily_demand(db, b.product_id, s.id)
            risk = evaluate_batch_risk(b.quantity, b.expiry_date, daily_demand)
            s_surplus += risk["surplus_quantity"]

        store_comparison.append({
            "store_id": s.id,
            "store_name": s.store_name.split("(")[0].strip(),
            "total_units": s_units,
            "surplus_units": s_surplus
        })

    # 6. Expiry distribution (by days bracket)
    today = func.current_date()
    expiry_brackets = {
        "0-7 days": 0,
        "8-14 days": 0,
        "15-30 days": 0,
        "30+ days": 0
    }
    from datetime import date
    for b in batches:
        days = (b.expiry_date - date.today()).days
        if days <= 7:
            expiry_brackets["0-7 days"] += b.quantity
        elif days <= 14:
            expiry_brackets["8-14 days"] += b.quantity
        elif days <= 30:
            expiry_brackets["15-30 days"] += b.quantity
        else:
            expiry_brackets["30+ days"] += b.quantity

    expiry_chart_data = [{"bracket": k, "units": v} for k, v in expiry_brackets.items()]

    return {
        "total_units": total_units,
        "total_products": total_products,
        "total_stores": total_stores,
        "high_risk_batches": high_risk_batches,
        "medium_risk_batches": med_risk_batches,
        "low_risk_batches": low_risk_batches,
        "surplus_inventory": surplus_units,
        "pending_recommendations": pending_recs,
        "approved_recommendations": approved_recs,
        "completed_transfers": completed_recs,
        "estimated_value_protected": impact["estimated_net_value_protected"],
        "impact_summary": impact,
        "store_comparison": store_comparison,
        "expiry_distribution": expiry_chart_data
    }

@router.post("/reset-demo-data")
def reset_demo_data(db: Session = Depends(get_db)):
    """Reset database to initial pristine hackathon demo dataset."""
    seed_database(db)
    return {
        "success": True,
        "message": "Demo data successfully reset to initial baseline state."
    }
