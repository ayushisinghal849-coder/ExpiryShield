from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.models.recommendation import Recommendation
from app.models.action import Action
from app.models.batch import Batch
from app.schemas.recommendation import (
    RecommendationApproveRequest, RecommendationRejectRequest, ActionCompleteRequest, RecommendationOut
)
from app.api.recommendations import get_recommendation_details

router = APIRouter(prefix="", tags=["Approvals & Execution"])

@router.post("/approve", response_model=dict)
def approve_recommendation(payload: RecommendationApproveRequest, db: Session = Depends(get_db)):
    """
    Approves a recommendation.
    Validates batch exists and has not already been completed.
    Creates an Action tracking record with PENDING execution status.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == payload.recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Recommendation has already been completed.")

    if rec.status == "REJECTED":
        raise HTTPException(status_code=400, detail="Cannot approve a previously rejected recommendation.")

    # Validate source batch still has sufficient stock
    batch = db.query(Batch).filter(Batch.id == rec.batch_id).first()
    if not batch or batch.quantity < rec.recommended_quantity:
        raise HTTPException(status_code=400, detail="Source batch no longer has sufficient stock available.")

    rec.status = "APPROVED"

    # Create or update Action record
    action = db.query(Action).filter(Action.recommendation_id == rec.id).first()
    if not action:
        action = Action(
            recommendation_id=rec.id,
            action_type=rec.action_type,
            approved_by=payload.approved_by or "Store Manager",
            execution_status="APPROVED",
            created_at=datetime.utcnow()
        )
        db.add(action)
    else:
        action.execution_status = "APPROVED"
        action.approved_by = payload.approved_by or "Store Manager"

    db.commit()
    return {
        "success": True,
        "message": f"Recommendation #{rec.id} ({rec.action_type}) approved successfully.",
        "status": "APPROVED",
        "action_id": action.id
    }

@router.post("/reject", response_model=dict)
def reject_recommendation(payload: RecommendationRejectRequest, db: Session = Depends(get_db)):
    """Rejects a pending recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == payload.recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Cannot reject a completed recommendation.")

    rec.status = "REJECTED"

    action = db.query(Action).filter(Action.recommendation_id == rec.id).first()
    if action:
        action.execution_status = "REJECTED"

    db.commit()
    return {
        "success": True,
        "message": f"Recommendation #{rec.id} rejected.",
        "status": "REJECTED"
    }

@router.post("/complete", response_model=dict)
def complete_transfer(payload: ActionCompleteRequest, db: Session = Depends(get_db)):
    """
    Executes and finalizes an approved recommendation inside a strict database transaction:
    - Verifies status is APPROVED (prevents unapproved execution)
    - Verifies not already COMPLETED (prevents duplicate execution)
    - For TRANSFER:
        - Decreases source batch stock (ensuring stock does not drop below 0)
        - Increases destination store batch stock (finds existing or creates matching batch)
    - Sets Recommendation status to COMPLETED
    - Sets Action execution_status to COMPLETED with completed_at timestamp
    """
    rec = db.query(Recommendation).filter(Recommendation.id == payload.recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if rec.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Transfer has already been completed. Duplicate execution prevented.")

    if rec.status != "APPROVED":
        raise HTTPException(status_code=400, detail=f"Cannot complete recommendation with status '{rec.status}'. Must be APPROVED first.")

    source_batch = db.query(Batch).filter(Batch.id == rec.batch_id).first()
    if not source_batch:
        raise HTTPException(status_code=404, detail="Source batch not found.")

    if source_batch.quantity < rec.recommended_quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient source stock ({source_batch.quantity} units available, {rec.recommended_quantity} required)."
        )

    # Perform inventory updates
    if rec.action_type == "TRANSFER":
        if not rec.destination_store_id:
            raise HTTPException(status_code=400, detail="Destination store missing for transfer.")

        # 1. Decrease source inventory
        source_batch.quantity -= rec.recommended_quantity

        # 2. Increase destination inventory
        dest_batch = (
            db.query(Batch)
            .filter(
                Batch.product_id == rec.product_id,
                Batch.store_id == rec.destination_store_id,
                Batch.expiry_date == source_batch.expiry_date
            )
            .first()
        )

        if dest_batch:
            dest_batch.quantity += rec.recommended_quantity
        else:
            dest_batch = Batch(
                product_id=rec.product_id,
                store_id=rec.destination_store_id,
                batch_code=f"{source_batch.batch_code}-TRX",
                quantity=rec.recommended_quantity,
                expiry_date=source_batch.expiry_date,
                received_date=datetime.utcnow().date()
            )
            db.add(dest_batch)

    elif rec.action_type in ["DISCOUNT", "BUNDLE", "FEFO"]:
        # Mark as completed action
        pass

    # Update statuses
    rec.status = "COMPLETED"

    action = db.query(Action).filter(Action.recommendation_id == rec.id).first()
    if not action:
        action = Action(
            recommendation_id=rec.id,
            action_type=rec.action_type,
            approved_by="Store Manager",
            execution_status="COMPLETED",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(action)
    else:
        action.execution_status = "COMPLETED"
        action.completed_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "message": f"Successfully completed {rec.action_type} for {rec.recommended_quantity} units.",
        "recommendation_id": rec.id,
        "action_type": rec.action_type,
        "quantity_moved": rec.recommended_quantity,
        "source_remaining_stock": source_batch.quantity,
        "execution_status": "COMPLETED"
    }

@router.get("/approvals", response_model=List[RecommendationOut])
def list_approvals(db: Session = Depends(get_db)):
    """List all recommendations that are pending, approved, or completed."""
    recs = db.query(Recommendation).order_by(Recommendation.id.desc()).all()
    results = []
    for r in recs:
        results.append(get_recommendation_details(r.id, db))
    return results
