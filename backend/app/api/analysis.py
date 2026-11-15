from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.models.batch import Batch
from app.models.product import Product
from app.models.store import Store
from app.schemas.analysis import AnalysisSummaryOut, AnalysisItemOut
from app.services.demand_service import calculate_average_daily_demand, calculate_expected_consumption
from app.services.risk_engine import evaluate_batch_risk

router = APIRouter(prefix="", tags=["Analysis & Expiry Risk"])

@router.post("/analyze", response_model=AnalysisSummaryOut)
def run_analysis(
    store_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Executes full inventory expiry risk analysis:
    - Calculates average daily demand from historical sales
    - Projects expected consumption before expiry
    - Computes surplus units at risk
    - Scores risk from 0-100 and classifies as LOW, MEDIUM, HIGH, EXPIRED
    - Generates human-readable explanation
    """
    query = (
        db.query(Batch, Product, Store)
        .join(Product, Batch.product_id == Product.id)
        .join(Store, Batch.store_id == Store.id)
        .filter(Batch.quantity > 0)
    )

    if store_id:
        query = query.filter(Batch.store_id == store_id)

    results = query.all()

    items = []
    high_count = 0
    med_count = 0
    low_count = 0
    expired_count = 0
    total_surplus_units = 0
    total_surplus_val = 0.0

    for batch, product, store in results:
        daily_demand = calculate_average_daily_demand(db, product.id, store.id)
        risk = evaluate_batch_risk(batch.quantity, batch.expiry_date, daily_demand)

        surplus = risk["surplus_quantity"]
        total_surplus_units += surplus
        total_surplus_val += round(surplus * product.selling_price, 2)

        level = risk["risk_level"]
        if level == "HIGH":
            high_count += 1
        elif level == "MEDIUM":
            med_count += 1
        elif level == "LOW":
            low_count += 1
        elif level == "EXPIRED":
            expired_count += 1

        items.append(AnalysisItemOut(
            batch_id=batch.id,
            batch_code=batch.batch_code,
            product_id=product.id,
            product_name=product.product_name,
            category=product.category,
            store_id=store.id,
            store_name=store.store_name,
            quantity=batch.quantity,
            selling_price=product.selling_price,
            cost_price=product.cost_price,
            expiry_date=batch.expiry_date,
            days_to_expiry=risk["days_to_expiry"],
            average_daily_demand=daily_demand,
            expected_consumption=risk["expected_consumption"],
            surplus_quantity=surplus,
            risk_score=risk["risk_score"],
            risk_level=level,
            explanation=risk["explanation"]
        ))

    items.sort(key=lambda x: (x.risk_score, -x.days_to_expiry), reverse=True)

    return AnalysisSummaryOut(
        total_batches=len(items),
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        expired_count=expired_count,
        total_surplus_units=total_surplus_units,
        total_surplus_value=round(total_surplus_val, 2),
        items=items
    )
