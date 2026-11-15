import pytest
from datetime import date, timedelta
from app.services.risk_engine import evaluate_batch_risk

def test_risk_scoring_expired():
    today = date.today()
    past_expiry = today - timedelta(days=5)
    risk = evaluate_batch_risk(quantity=50, expiry_date=past_expiry, average_daily_demand=5.0, current_date=today)
    assert risk["risk_level"] == "EXPIRED"
    assert risk["risk_score"] == 100.0
    assert risk["surplus_quantity"] == 50

def test_risk_scoring_high_surplus():
    today = date.today()
    # 7 days to expiry, 100 units in stock, demand 3 units/day -> expected consumption 21, surplus 79
    expiry = today + timedelta(days=7)
    risk = evaluate_batch_risk(quantity=100, expiry_date=expiry, average_daily_demand=3.0, current_date=today)
    assert risk["risk_level"] == "HIGH"
    assert risk["surplus_quantity"] == 79
    assert risk["expected_consumption"] == 21.0
    assert risk["risk_score"] > 60

def test_risk_scoring_low_balanced():
    today = date.today()
    # 30 days to expiry, 30 units in stock, demand 2 units/day -> expected consumption 60, surplus 0
    expiry = today + timedelta(days=30)
    risk = evaluate_batch_risk(quantity=30, expiry_date=expiry, average_daily_demand=2.0, current_date=today)
    assert risk["risk_level"] == "LOW"
    assert risk["surplus_quantity"] == 0
