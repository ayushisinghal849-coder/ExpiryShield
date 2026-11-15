from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.recommendation import Recommendation
from app.models.product import Product
from app.models.batch import Batch
from app.models.store import Store
from app.schemas.recommendation import (
    RecommendationOut, RecommendationApproveRequest, RecommendationRejectRequest, AlternativeAction
)
from app.services.action_ranking import rank_and_generate_recommendations

router = APIRouter(prefix="", tags=["Recommendations"])

@router.get("/recommend", response_model=List[RecommendationOut])
def get_recommendations(db: Session = Depends(get_db)):
    """
    Generates and returns ranked recommendations comparing Transfer, Discount, Bundle, FEFO, and Procure Less.
    Syncs generated recommendations into the persistent Recommendation database table.
    """
    generated = rank_and_generate_recommendations(db)

    # Sync into database to persist recommendation state
    result_out = []
    for g in generated:
        # Check if recommendation already exists for this batch and action
        existing = (
            db.query(Recommendation)
            .filter(
                Recommendation.batch_id == g["batch_id"],
                Recommendation.action_type == g["action_type"],
                Recommendation.source_store_id == g["source_store_id"]
            )
            .first()
        )

        if not existing:
            rec = Recommendation(
                source_store_id=g["source_store_id"],
                destination_store_id=g["destination_store_id"],
                product_id=g["product_id"],
                batch_id=g["batch_id"],
                recommended_quantity=g["recommended_quantity"],
                action_type=g["action_type"],
                expected_value=g["expected_value"],
                estimated_cost=g["estimated_cost"],
                distance_km=g["distance_km"],
                risk_score=g["risk_score"],
                reason=g["reason"],
                status="PENDING"
            )
            db.add(rec)
            db.flush()
            rec_id = rec.id
            status = "PENDING"
        else:
            rec_id = existing.id
            status = existing.status

        alts = [AlternativeAction(**a) for a in g.get("alternatives", [])]

        result_out.append(RecommendationOut(
            id=rec_id,
            source_store_id=g["source_store_id"],
            source_store_name=g["source_store_name"],
            destination_store_id=g["destination_store_id"],
            destination_store_name=g["destination_store_name"],
            product_id=g["product_id"],
            product_name=g["product_name"],
            batch_id=g["batch_id"],
            batch_code=g["batch_code"],
            recommended_quantity=g["recommended_quantity"],
            action_type=g["action_type"],
            expected_value=g["expected_value"],
            estimated_cost=g["estimated_cost"],
            net_benefit=g["net_benefit"],
            distance_km=g["distance_km"],
            risk_score=g["risk_score"],
            reason=g["reason"],
            status=status,
            ranking=g["ranking"],
            alternatives=alts
        ))

    db.commit()
    return result_out

@router.get("/recommendations/{id}", response_model=RecommendationOut)
def get_recommendation_details(id: int, db: Session = Depends(get_db)):
    """Get detailed information for a single recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    src_store = db.query(Store).filter(Store.id == rec.source_store_id).first()
    dest_store = db.query(Store).filter(Store.id == rec.destination_store_id).first() if rec.destination_store_id else None
    product = db.query(Product).filter(Product.id == rec.product_id).first()
    batch = db.query(Batch).filter(Batch.id == rec.batch_id).first()

    net_ben = round(rec.expected_value - rec.estimated_cost, 2)
    return RecommendationOut(
        id=rec.id,
        source_store_id=rec.source_store_id,
        source_store_name=src_store.store_name if src_store else "",
        destination_store_id=rec.destination_store_id,
        destination_store_name=dest_store.store_name if dest_store else None,
        product_id=rec.product_id,
        product_name=product.product_name if product else "",
        batch_id=rec.batch_id,
        batch_code=batch.batch_code if batch else "",
        recommended_quantity=rec.recommended_quantity,
        action_type=rec.action_type,
        expected_value=rec.expected_value,
        estimated_cost=rec.estimated_cost,
        net_benefit=net_ben,
        distance_km=rec.distance_km,
        risk_score=rec.risk_score,
        reason=rec.reason,
        status=rec.status,
        ranking=1,
        alternatives=[]
    )
