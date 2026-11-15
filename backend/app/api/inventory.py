from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import csv
import io

from app.core.database import get_db
from app.models.product import Product
from app.models.batch import Batch
from app.models.store import Store
from app.models.sale import Sale
from app.models.recommendation import Recommendation
from app.models.action import Action
from app.schemas.inventory import (
    ProductCreate, ProductOut, BatchCreate, BatchUpdate, BatchOut, InventoryItemOut
)
from app.services.demand_service import calculate_average_daily_demand
from app.services.risk_engine import evaluate_batch_risk

router = APIRouter(prefix="", tags=["Inventory & Batches"])

@router.get("/inventory", response_model=List[InventoryItemOut])
def get_inventory(
    store_id: Optional[int] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all inventory items with batch details, real-time risk scores, and store info.
    Supports filtering by store, category, risk level, and text search.
    """
    query = (
        db.query(Batch, Product, Store)
        .join(Product, Batch.product_id == Product.id)
        .join(Store, Batch.store_id == Store.id)
    )

    if store_id:
        query = query.filter(Batch.store_id == store_id)
    if category:
        query = query.filter(Product.category == category)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Product.product_name.ilike(search_pattern)) |
            (Batch.batch_code.ilike(search_pattern))
        )

    results = query.all()
    items = []
    
    for batch, product, store in results:
        daily_demand = calculate_average_daily_demand(db, product.id, store.id)
        risk = evaluate_batch_risk(batch.quantity, batch.expiry_date, daily_demand)

        if risk_level and risk["risk_level"].upper() != risk_level.upper():
            continue

        items.append(InventoryItemOut(
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
            risk_level=risk["risk_level"],
            risk_score=risk["risk_score"]
        ))

    # Sort by days to expiry ascending
    items.sort(key=lambda x: x.days_to_expiry)
    return items

@router.post("/inventory", response_model=BatchOut)
def create_batch(batch_in: BatchCreate, db: Session = Depends(get_db)):
    """Add a new batch to inventory."""
    # Verify product and store exist
    product = db.query(Product).filter(Product.id == batch_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    store = db.query(Store).filter(Store.id == batch_in.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    new_batch = Batch(
        product_id=batch_in.product_id,
        store_id=batch_in.store_id,
        batch_code=batch_in.batch_code,
        quantity=batch_in.quantity,
        expiry_date=batch_in.expiry_date,
        received_date=batch_in.received_date or date.today()
    )
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch

@router.put("/inventory/{id}", response_model=BatchOut)
def update_batch(id: int, batch_update: BatchUpdate, db: Session = Depends(get_db)):
    """Update an existing batch's quantity or expiry date."""
    batch = db.query(Batch).filter(Batch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch_update.quantity is not None:
        if batch_update.quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity cannot be negative")
        batch.quantity = batch_update.quantity

    if batch_update.expiry_date is not None:
        batch.expiry_date = batch_update.expiry_date

    db.commit()
    db.refresh(batch)
    return batch

@router.post("/products", response_model=ProductOut)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to catalogue."""
    new_product = Product(
        product_name=product_in.product_name,
        category=product_in.category,
        selling_price=product_in.selling_price,
        cost_price=product_in.cost_price
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/products", response_model=List[ProductOut])
def get_products(db: Session = Depends(get_db)):
    """List all products in catalogue."""
    return db.query(Product).all()

@router.post("/inventory/upload-csv")
async def upload_inventory_csv(file: UploadFile = File(...), replace_existing: bool = True, db: Session = Depends(get_db)):
    """
    Import inventory items via CSV file with field validation and error reporting.
    Expected CSV columns: product_name, category, selling_price, cost_price, store_name, batch_code, quantity, expiry_date
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
    if replace_existing:
        # For the hackathon prototype, importing a CSV means analysing that dataset
        # on its own, not mixing it with the previous sample/workspace output.
        db.query(Action).delete()
        db.query(Recommendation).delete()
        db.query(Sale).delete()
        db.query(Batch).delete()
        db.query(Product).delete()
        db.query(Store).delete()
        db.flush()
    imported = 0
    rejected = 0
    errors = []

    for row_idx, row in enumerate(rows, start=2):
        try:
            prod_name = row.get("product_name", "").strip()
            category = row.get("category", "General").strip()
            selling_price = float(row.get("selling_price", 100))
            cost_price = float(row.get("cost_price", 70))
            store_name = row.get("store_name", "").strip()
            batch_code = row.get("batch_code", "").strip()
            quantity = int(row.get("quantity", 0))
            expiry_str = row.get("expiry_date", "").strip()
            daily_sales = float(row.get("daily_sales_per_day", row.get("daily_sales", 0)) or 0)

            if not prod_name or not store_name or not batch_code or not expiry_str:
                rejected += 1
                errors.append(f"Row {row_idx}: Missing required fields (product, store, batch, or expiry).")
                continue

            if quantity < 0 or selling_price < 0 or cost_price < 0:
                rejected += 1
                errors.append(f"Row {row_idx}: Quantity and prices must be positive.")
                continue

            from datetime import datetime
            try:
                expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            except ValueError:
                expiry_dt = datetime.strptime(expiry_str, "%d/%m/%Y").date()

            # Find or create Product
            product = db.query(Product).filter(Product.product_name == prod_name).first()
            if not product:
                product = Product(
                    product_name=prod_name,
                    category=category,
                    selling_price=selling_price,
                    cost_price=cost_price
                )
                db.add(product)
                db.flush()

            # Find or create Store
            store = db.query(Store).filter(Store.store_name.ilike(f"%{store_name}%")).first()
            if not store:
                known_locations = {
                    "Store A - Central Market": (28.6328, 77.2197),
                    "Store B - Karol Bagh": (28.6519, 77.1909),
                    "Store C - Dwarka": (28.5921, 77.0460),
                    "Store D - Agra": (27.1767, 78.0081),
                }
                latitude, longitude = known_locations.get(store_name, (28.6139, 77.2090))
                store = Store(
                    store_name=store_name,
                    location=store_name,
                    latitude=latitude,
                    longitude=longitude
                )
                db.add(store)
                db.flush()

            # Check if batch exists; update or create
            batch = db.query(Batch).filter(Batch.batch_code == batch_code, Batch.store_id == store.id).first()
            if batch:
                batch.quantity = quantity
                batch.expiry_date = expiry_dt
            else:
                batch = Batch(
                    product_id=product.id,
                    store_id=store.id,
                    batch_code=batch_code,
                    quantity=quantity,
                    expiry_date=expiry_dt,
                    received_date=date.today()
                )
                db.add(batch)

            # Optional sample-data field: create 30 days of sales history so analysis
            # changes according to the selected/uploaded dataset instead of using fixed demo values.
            if daily_sales > 0:
                db.query(Sale).filter(Sale.product_id == product.id, Sale.store_id == store.id).delete()
                for day in range(1, 31):
                    db.add(Sale(product_id=product.id, store_id=store.id,
                                quantity_sold=max(0, int(round(daily_sales))),
                                sale_date=date.today() - timedelta(days=day)))
            imported += 1
        except Exception as e:
            rejected += 1
            errors.append(f"Row {row_idx}: {str(e)}")

    db.commit()
    return {
        "success": True,
        "imported_records": imported,
        "rejected_records": rejected,
        "errors": errors[:10] # Show first 10 errors
    }
