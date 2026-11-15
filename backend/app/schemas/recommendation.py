from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AlternativeAction(BaseModel):
    action_type: str
    expected_value: float
    estimated_cost: float
    net_benefit: float
    feasibility: str
    description: str

class RecommendationOut(BaseModel):
    id: int
    source_store_id: int
    source_store_name: str
    destination_store_id: Optional[int] = None
    destination_store_name: Optional[str] = None
    product_id: int
    product_name: str
    batch_id: int
    batch_code: str
    recommended_quantity: int
    action_type: str # TRANSFER, DISCOUNT, BUNDLE, FEFO, PROCURE_LESS
    expected_value: float
    estimated_cost: float
    net_benefit: float
    distance_km: float
    risk_score: float
    reason: str
    status: str # PENDING, APPROVED, REJECTED, COMPLETED
    ranking: int = 1
    alternatives: List[AlternativeAction] = []
    model_config = ConfigDict(from_attributes=True)

class RecommendationApproveRequest(BaseModel):
    recommendation_id: int
    approved_by: Optional[str] = "Store Manager"

class RecommendationRejectRequest(BaseModel):
    recommendation_id: int
    reason: Optional[str] = "Rejected by Manager"

class ActionCompleteRequest(BaseModel):
    recommendation_id: int
