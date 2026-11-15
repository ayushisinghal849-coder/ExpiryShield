from pydantic import BaseModel
from typing import Optional
from datetime import date

class AnalysisItemOut(BaseModel):
    batch_id: int
    batch_code: str
    product_id: int
    product_name: str
    category: str
    store_id: int
    store_name: str
    quantity: int
    selling_price: float
    cost_price: float
    expiry_date: date
    days_to_expiry: int
    average_daily_demand: float
    expected_consumption: float
    surplus_quantity: int
    risk_score: float
    risk_level: str # LOW, MEDIUM, HIGH, EXPIRED
    explanation: str

class AnalysisSummaryOut(BaseModel):
    total_batches: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    expired_count: int
    total_surplus_units: int
    total_surplus_value: float
    items: list[AnalysisItemOut]
