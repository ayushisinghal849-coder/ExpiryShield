from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date

class ProductBase(BaseModel):
    product_name: str
    category: str
    selling_price: float
    cost_price: float

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BatchBase(BaseModel):
    product_id: int
    store_id: int
    batch_code: str
    quantity: int
    expiry_date: date
    received_date: Optional[date] = None

class BatchCreate(BatchBase):
    pass

class BatchUpdate(BaseModel):
    quantity: Optional[int] = None
    expiry_date: Optional[date] = None

class BatchOut(BatchBase):
    id: int
    product: Optional[ProductOut] = None
    model_config = ConfigDict(from_attributes=True)

class InventoryItemOut(BaseModel):
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
    risk_level: str
    risk_score: float
    model_config = ConfigDict(from_attributes=True)
