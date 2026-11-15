from datetime import date
from typing import Dict, Any, Tuple

def evaluate_batch_risk(
    quantity: int,
    expiry_date: date,
    average_daily_demand: float,
    current_date: date = None
) -> Dict[str, Any]:
    """
    Evaluates expiry risk using deterministic, transparent rules:
    - Days until expiry = expiry_date - current_date
    - Expected consumption = average_daily_demand * days_until_expiry
    - Surplus quantity = max(0, quantity - round(expected_consumption))
    - Risk score: 0 to 100 based on urgency and surplus proportion
    - Risk Level: LOW, MEDIUM, HIGH, EXPIRED
    """
    if current_date is None:
        current_date = date.today()

    days_until_expiry = (expiry_date - current_date).days

    # Expired inventory
    if days_until_expiry < 0:
        return {
            "days_to_expiry": days_until_expiry,
            "expected_consumption": 0.0,
            "surplus_quantity": quantity,
            "risk_score": 100.0,
            "risk_level": "EXPIRED",
            "explanation": f"Batch expired {abs(days_until_expiry)} days ago. 100% of remaining stock ({quantity} units) is unsellable."
        }

    # Zero stock batch
    if quantity <= 0:
        return {
            "days_to_expiry": days_until_expiry,
            "expected_consumption": 0.0,
            "surplus_quantity": 0,
            "risk_score": 0.0,
            "risk_level": "LOW",
            "explanation": "Zero units in stock. No expiry loss risk."
        }

    # Expected consumption before expiry
    expected_consumption = round(average_daily_demand * days_until_expiry, 2)
    surplus_quantity = max(0, quantity - int(math_floor(expected_consumption)))

    # Risk Scoring Model:
    # 1. Time Factor (0 - 50 points): closer to expiry -> higher urgency
    if days_until_expiry <= 3:
        time_factor = 50.0
    elif days_until_expiry <= 7:
        time_factor = 40.0
    elif days_until_expiry <= 15:
        time_factor = 30.0
    elif days_until_expiry <= 30:
        time_factor = 20.0
    elif days_until_expiry <= 60:
        time_factor = 10.0
    else:
        time_factor = 0.0

    # 2. Surplus Proportion Factor (0 - 50 points): proportion of stock that won't sell
    surplus_ratio = surplus_quantity / quantity if quantity > 0 else 0.0
    surplus_factor = min(50.0, surplus_ratio * 50.0)

    # Base risk score
    risk_score = round(time_factor + surplus_factor, 1)

    # Risk Level classification
    if days_until_expiry <= 0:
        risk_level = "EXPIRED"
        risk_score = 100.0
    elif risk_score >= 65 or (days_until_expiry <= 7 and surplus_quantity > 0):
        risk_level = "HIGH"
    elif risk_score >= 35 or (days_until_expiry <= 20 and surplus_quantity > 0):
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Explanation generator
    if surplus_quantity > 0:
        explanation = (
            f"At demand of {average_daily_demand} units/day, only ~{int(expected_consumption)} "
            f"of {quantity} units will sell before expiry in {days_until_expiry} days. "
            f"Surplus of {surplus_quantity} units at risk."
        )
    else:
        explanation = (
            f"Inventory ({quantity} units) is well-balanced. Projected demand ({int(expected_consumption)} units) "
            f"will clear stock within {days_until_expiry} days."
        )

    return {
        "days_to_expiry": days_until_expiry,
        "expected_consumption": expected_consumption,
        "surplus_quantity": surplus_quantity,
        "risk_score": min(100.0, max(0.0, risk_score)),
        "risk_level": risk_level,
        "explanation": explanation
    }

def math_floor(val: float) -> int:
    import math
    return int(math.floor(val))
