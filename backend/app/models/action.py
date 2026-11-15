from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    approved_by = Column(String(100), default="Store Manager")
    execution_status = Column(String(50), default="PENDING") # PENDING, IN_PROGRESS, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    recommendation = relationship("Recommendation", back_populates="actions")
