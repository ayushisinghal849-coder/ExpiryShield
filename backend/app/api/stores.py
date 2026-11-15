from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreOut

router = APIRouter(prefix="/stores", tags=["Stores"])

@router.get("", response_model=List[StoreOut])
def get_stores(db: Session = Depends(get_db)):
    """List all registered retail stores."""
    return db.query(Store).all()

@router.post("", response_model=StoreOut)
def create_store(store_in: StoreCreate, db: Session = Depends(get_db)):
    """Register a new retail store with geographic coordinates."""
    new_store = Store(
        store_name=store_in.store_name,
        location=store_in.location,
        latitude=store_in.latitude,
        longitude=store_in.longitude
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    return new_store
