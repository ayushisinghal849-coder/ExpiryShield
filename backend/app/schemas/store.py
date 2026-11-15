from pydantic import BaseModel, ConfigDict
from typing import Optional

class StoreBase(BaseModel):
    store_name: str
    location: str
    latitude: float
    longitude: float

class StoreCreate(StoreBase):
    pass

class StoreOut(StoreBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
