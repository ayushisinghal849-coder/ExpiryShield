from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.store import Store
from app.models.product import Product
from app.models.batch import Batch
from app.models.sale import Sale
from app.models.recommendation import Recommendation
from app.models.action import Action

def seed_database(db: Session = None):
    """
    Seeds database with realistic retail scenario data including the exact primary demo scenario:
    - Product: Milk Powder (Selling Price: Rs 200, Cost: Rs 140)
    - Store A: 100 units, avg daily demand 3 units, 7 days to expiry (expected consumption 21, surplus 79)
    - Store B: 20 units, avg daily demand 12 units, 7 days to expiry (expected demand 84, shortage gap 64)
    - Haversine Distance: ~8.0 km, transfer cost Rs 400
    - Transferred: 64 units -> Revenue protected: 64 * 200 = 12,800; Net benefit: 12,400.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Clear existing data safely
        db.query(Action).delete()
        db.query(Recommendation).delete()
        db.query(Sale).delete()
        db.query(Batch).delete()
        db.query(Product).delete()
        db.query(Store).delete()
        db.commit()

        # 1. Create Stores
        # Store A: Indiranagar, Bangalore (12.9784, 77.6408)
        # Store B: Koramangala, Bangalore (12.9352, 77.6245) -> ~5-8 km distance
        # Store C: Whitefield, Bangalore (12.9698, 77.7500) -> ~12 km distance
        store_a = Store(
            store_name="Store A (Indiranagar Supercenter)",
            location="100 Feet Road, Indiranagar, Bengaluru",
            latitude=12.9784,
            longitude=77.6408
        )
        store_b = Store(
            store_name="Store B (Koramangala Metro Mart)",
            location="80 Feet Road, 4th Block, Koramangala, Bengaluru",
            latitude=12.9352,
            longitude=77.6998
        )
        store_c = Store(
            store_name="Store C (Whitefield Hypermarket)",
            location="ITPL Main Road, Whitefield, Bengaluru",
            latitude=12.9698,
            longitude=77.7500
        )
        db.add_all([store_a, store_b, store_c])
        db.commit()

        # 2. Create Products
        p_milk_powder = Product(
            product_name="Milk Powder (500g)",
            category="Dairy & Breakfast",
            selling_price=200.0,
            cost_price=140.0
        )
        p_greek_yogurt = Product(
            product_name="Greek Yogurt Strawberry (200g)",
            category="Dairy & Chilled",
            selling_price=90.0,
            cost_price=55.0
        )
        p_almond_milk = Product(
            product_name="Organic Almond Milk (1L)",
            category="Plant Beverages",
            selling_price=250.0,
            cost_price=180.0
        )
        p_butter = Product(
            product_name="Farm Butter Unsalted (500g)",
            category="Dairy & Chilled",
            selling_price=260.0,
            cost_price=190.0
        )
        p_cheese_slices = Product(
            product_name="Cheddar Cheese Slices (200g)",
            category="Dairy & Chilled",
            selling_price=160.0,
            cost_price=110.0
        )
        db.add_all([p_milk_powder, p_greek_yogurt, p_almond_milk, p_butter, p_cheese_slices])
        db.commit()

        # 3. Create Batches
        today = date.today()

        # Primary Demo Batches:
        # Store A: Milk Powder 100 units, expiring in 7 days
        batch_a_milk = Batch(
            product_id=p_milk_powder.id,
            store_id=store_a.id,
            batch_code="MP-IND-0701",
            quantity=100,
            expiry_date=today + timedelta(days=7),
            received_date=today - timedelta(days=23)
        )
        # Store B: Milk Powder 20 units, expiring in 7 days
        batch_b_milk = Batch(
            product_id=p_milk_powder.id,
            store_id=store_b.id,
            batch_code="MP-KOR-0702",
            quantity=20,
            expiry_date=today + timedelta(days=7),
            received_date=today - timedelta(days=23)
        )

        # Other realistic batches:
        # Store A: Greek Yogurt with 3 days to expiry (Markdown candidate)
        batch_a_yogurt = Batch(
            product_id=p_greek_yogurt.id,
            store_id=store_a.id,
            batch_code="GY-IND-0301",
            quantity=45,
            expiry_date=today + timedelta(days=3),
            received_date=today - timedelta(days=12)
        )

        # Store C: Organic Almond Milk with 6 days to expiry
        batch_c_almond = Batch(
            product_id=p_almond_milk.id,
            store_id=store_c.id,
            batch_code="AM-WHI-0601",
            quantity=60,
            expiry_date=today + timedelta(days=6),
            received_date=today - timedelta(days=20)
        )

        # Store A: Cheddar Cheese with 30 days (Healthy low risk)
        batch_a_cheese = Batch(
            product_id=p_cheese_slices.id,
            store_id=store_a.id,
            batch_code="CS-IND-3001",
            quantity=35,
            expiry_date=today + timedelta(days=30),
            received_date=today - timedelta(days=5)
        )

        # Store B: Farm Butter with 40 days (Healthy low risk)
        batch_b_butter = Batch(
            product_id=p_butter.id,
            store_id=store_b.id,
            batch_code="FB-KOR-4001",
            quantity=50,
            expiry_date=today + timedelta(days=40),
            received_date=today - timedelta(days=4)
        )

        db.add_all([batch_a_milk, batch_b_milk, batch_a_yogurt, batch_c_almond, batch_a_cheese, batch_b_butter])
        db.commit()

        # 4. Create Historical Sales (for demand forecasting over past 30 days)
        # Requirement:
        # Store A Milk Powder: avg 3 units/day (30 days * 3 = 90 units)
        # Store B Milk Powder: avg 12 units/day (30 days * 12 = 360 units)
        sales = []
        for i in range(1, 31):
            sale_dt = today - timedelta(days=i)
            # Store A: exactly 3 units / day
            sales.append(Sale(
                product_id=p_milk_powder.id,
                store_id=store_a.id,
                quantity_sold=3,
                sale_date=sale_dt
            ))
            # Store B: exactly 12 units / day
            sales.append(Sale(
                product_id=p_milk_powder.id,
                store_id=store_b.id,
                quantity_sold=12,
                sale_date=sale_dt
            ))
            # Store A Yogurt: ~2 units / day
            sales.append(Sale(
                product_id=p_greek_yogurt.id,
                store_id=store_a.id,
                quantity_sold=2,
                sale_date=sale_dt
            ))
            # Store C Almond Milk: ~3 units / day
            sales.append(Sale(
                product_id=p_almond_milk.id,
                store_id=store_c.id,
                quantity_sold=3,
                sale_date=sale_dt
            ))
            # Store A Almond Milk: ~10 units / day (Demand gap candidate for Store C surplus)
            sales.append(Sale(
                product_id=p_almond_milk.id,
                store_id=store_a.id,
                quantity_sold=10,
                sale_date=sale_dt
            ))

        db.add_all(sales)
        db.commit()

        print("ExpiryShield Demo Data Seeded Successfully!")
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_database()
