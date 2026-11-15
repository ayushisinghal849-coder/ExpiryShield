import pytest
from datetime import date, timedelta
from app.core.database import SessionLocal, Base, engine
from app.models.store import Store
from app.models.product import Product
from app.models.batch import Batch
from app.models.sale import Sale
from app.services.demand_service import calculate_average_daily_demand, calculate_expected_consumption

from app.seed.demo_data import seed_database

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_database(session)
    yield session
    session.close()

def test_demand_calculation(db):
    product = db.query(Product).filter(Product.product_name.like("%Milk Powder%")).first()
    store_a = db.query(Store).filter(Store.store_name.like("%Store A%")).first()
    store_b = db.query(Store).filter(Store.store_name.like("%Store B%")).first()

    assert product is not None
    assert store_a is not None
    assert store_b is not None

    demand_a = calculate_average_daily_demand(db, product.id, store_a.id)
    demand_b = calculate_average_daily_demand(db, product.id, store_b.id)

    # In our deterministic seed, Store A sells 3 units/day, Store B sells 12 units/day
    assert demand_a == 3.0
    assert demand_b == 12.0

    exp_cons_a = calculate_expected_consumption(demand_a, 7)
    assert exp_cons_a == 21.0
