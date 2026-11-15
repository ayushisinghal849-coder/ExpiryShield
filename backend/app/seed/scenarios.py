from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.store import Store
from app.models.product import Product
from app.models.batch import Batch
from app.models.sale import Sale
from app.models.recommendation import Recommendation
from app.models.action import Action

SCENARIOS = [
    {"id":"transfer-opportunity","name":"1. Cross-store transfer opportunity","description":"High surplus at Store A and strong demand gap at nearby Store B. Best for demonstrating store matching and transfer.","focus":"TRANSFER"},
    {"id":"urgent-discount","name":"2. Near-expiry discount scenario","description":"A short shelf-life batch with no feasible transfer window. The engine should prioritize a markdown.","focus":"DISCOUNT"},
    {"id":"fefo-rotation","name":"3. FEFO stock rotation scenario","description":"Inventory has a manageable shelf-life window and no destination shortage. Prioritize earliest-expiring stock.","focus":"FEFO"},
    {"id":"bundle-opportunity","name":"4. Bundle promotion scenario","description":"High surplus with a short but viable selling window. The engine should recommend a bundle promotion.","focus":"BUNDLE"},
    {"id":"remote-store","name":"5. Remote store / transfer not feasible","description":"A destination has demand, but distance makes transfer uneconomical. Use an in-store action instead.","focus":"FEFO"},
]

STORE_COORDS = {
    "Store A - Central Market": (28.6328, 77.2197, "Central Market, New Delhi"),
    "Store B - Karol Bagh": (28.6519, 77.1909, "Karol Bagh, New Delhi"),
    "Store C - Dwarka": (28.5921, 77.0460, "Dwarka, New Delhi"),
    "Store D - Agra": (27.1767, 78.0081, "Agra, Uttar Pradesh"),
}

# Each tuple: product, category, selling price, cost price, batch code, store key, qty, expiry days, daily sales
SCENARIO_ROWS = {
    "transfer-opportunity": [
        ("A2 Cow Milk Powder 500g", "Dairy", 240, 165, "TR-MILK-A", "A", 120, 8, 2),
        ("A2 Cow Milk Powder 500g", "Dairy", 240, 165, "TR-MILK-B", "B", 15, 10, 10),
        ("A2 Cow Milk Powder 500g", "Dairy", 240, 165, "TR-MILK-C", "C", 35, 18, 2),
    ],
    "urgent-discount": [
        ("Whole Wheat Bread", "Bakery", 55, 32, "DS-BREAD-A", "A", 90, 2, 4),
        ("Whole Wheat Bread", "Bakery", 55, 32, "DS-BREAD-B", "B", 25, 12, 1),
        ("Whole Wheat Bread", "Bakery", 55, 32, "DS-BREAD-C", "C", 20, 15, 1),
    ],
    "fefo-rotation": [
        ("Cheddar Cheese Slices 200g", "Dairy", 180, 118, "FE-CHEESE-A", "A", 70, 16, 1),
        ("Cheddar Cheese Slices 200g", "Dairy", 180, 118, "FE-CHEESE-B", "B", 25, 20, 1),
        ("Cheddar Cheese Slices 200g", "Dairy", 180, 118, "FE-CHEESE-C", "C", 30, 24, 1),
    ],
    "bundle-opportunity": [
        ("Orange Juice 1L", "Beverages", 130, 78, "BU-JUICE-A", "A", 110, 6, 2),
        ("Orange Juice 1L", "Beverages", 130, 78, "BU-JUICE-B", "B", 30, 15, 1),
        ("Orange Juice 1L", "Beverages", 130, 78, "BU-JUICE-C", "C", 25, 18, 1),
    ],
    "remote-store": [
        ("Organic Almond Milk 1L", "Plant Beverages", 220, 150, "RM-ALMOND-A", "A", 100, 12, 2),
        ("Organic Almond Milk 1L", "Plant Beverages", 220, 150, "RM-ALMOND-D", "D", 12, 14, 9),
        ("Organic Almond Milk 1L", "Plant Beverages", 220, 150, "RM-ALMOND-B", "B", 20, 20, 1),
    ],
}

def load_scenario(db: Session, scenario_id: str):
    if scenario_id not in SCENARIO_ROWS:
        raise ValueError("Unknown demo scenario")
    # Clear transactional and inventory records in FK-safe order.
    db.query(Action).delete()
    db.query(Recommendation).delete()
    db.query(Sale).delete()
    db.query(Batch).delete()
    db.query(Product).delete()
    db.query(Store).delete()
    db.flush()

    stores = {}
    required_store_keys = {row[5] for row in SCENARIO_ROWS[scenario_id]}
    for short in sorted(required_store_keys):
        key = next(k for k in STORE_COORDS if k.startswith(f"Store {short} -"))
        lat, lon, location = STORE_COORDS[key]
        store = Store(store_name=key, location=location, latitude=lat, longitude=lon)
        db.add(store)
        db.flush()
        stores[short] = store

    products = {}
    today = date.today()
    for idx, row in enumerate(SCENARIO_ROWS[scenario_id], start=1):
        name, category, price, cost, batch_code, store_key, qty, expiry_days, daily_sales = row
        if name not in products:
            product = Product(product_name=name, category=category, selling_price=price, cost_price=cost)
            db.add(product)
            db.flush()
            products[name] = product
        product = products[name]
        store = stores[store_key]
        batch = Batch(product_id=product.id, store_id=store.id, batch_code=batch_code,
                      quantity=qty, expiry_date=today + timedelta(days=expiry_days),
                      received_date=today - timedelta(days=10))
        db.add(batch)
        # 30 days of distinct historical sales per product/store drive demand calculations.
        for day in range(1, 31):
            db.add(Sale(product_id=product.id, store_id=store.id, quantity_sold=daily_sales,
                        sale_date=today - timedelta(days=day)))
    db.commit()
    return {"success": True, "scenario_id": scenario_id, "scenario": next(x for x in SCENARIOS if x["id"] == scenario_id),
            "stores_loaded": len(stores), "products_loaded": len(products), "batches_loaded": len(SCENARIO_ROWS[scenario_id])}
