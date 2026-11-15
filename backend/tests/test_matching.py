import pytest
from app.services.distance_service import calculate_haversine_distance, calculate_transport_cost
from app.services.matching_engine import find_cross_store_matches
from app.core.database import SessionLocal, Base, engine

from app.seed.demo_data import seed_database

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    seed_database(session)
    yield session
    session.close()

def test_haversine_distance_and_cost():
    # Store A (12.9784, 77.6408) to Store B (12.9352, 77.6998)
    dist = calculate_haversine_distance(12.9784, 77.6408, 12.9352, 77.6998)
    assert dist == 8.0 # Exact 8.0 km

    cost = calculate_transport_cost(dist)
    assert cost == 400.0 # 200 base + 8*25 = 400

def test_cross_store_matching_milk_powder(db):
    matches = find_cross_store_matches(db)
    milk_match = [m for m in matches if "Milk Powder" in m["product"].product_name]
    assert len(milk_match) >= 1
    m = milk_match[0]

    # Verification of primary hackathon scenario:
    # Recommended quantity: MIN(Source Surplus 79, Destination Gap 64) = 64
    assert m["transfer_quantity"] == 64
    assert m["distance_km"] == 8.0
    assert m["transport_cost"] == 400.0
    # Expected value: 64 * 200 = 12,800
    assert m["expected_value"] == 12800.0
    # Net benefit: 12,800 - 400 = 12,400
    assert m["net_benefit"] == 12400.0
