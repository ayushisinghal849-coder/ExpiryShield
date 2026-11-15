import pandas as pd
from datetime import date, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.models.sale import Sale

def calculate_average_daily_demand(
    db: Session,
    product_id: int,
    store_id: int,
    lookback_days: int = 30
) -> float:
    """
    Calculate Average Daily Demand using historical sales data:
    Average Daily Demand = Total units sold in historical period / Number of days.
    """
    start_date = date.today() - timedelta(days=lookback_days)
    
    sales_records = (
        db.query(Sale)
        .filter(
            Sale.product_id == product_id,
            Sale.store_id == store_id,
            Sale.sale_date >= start_date
        )
        .all()
    )

    if not sales_records:
        # Fallback to any sales if recent sales are empty
        sales_records = (
            db.query(Sale)
            .filter(
                Sale.product_id == product_id,
                Sale.store_id == store_id
            )
            .all()
        )

    if not sales_records:
        return 0.0

    # Build DataFrame
    data = [{"quantity_sold": s.quantity_sold, "sale_date": s.sale_date} for s in sales_records]
    df = pd.DataFrame(data)

    total_units_sold = float(df["quantity_sold"].sum())
    
    # Calculate period length in days (minimum 1 day)
    min_date = df["sale_date"].min()
    max_date = df["sale_date"].max()
    date_range_days = max((max_date - min_date).days + 1, lookback_days)

    if date_range_days <= 0:
        date_range_days = 1

    daily_demand = total_units_sold / date_range_days
    return round(daily_demand, 2)


def calculate_expected_consumption(
    daily_demand: float,
    days_until_expiry: int
) -> float:
    """
    Expected Consumption = Average Daily Demand × Days Until Expiry
    """
    if days_until_expiry <= 0:
        return 0.0
    return round(daily_demand * days_until_expiry, 2)
