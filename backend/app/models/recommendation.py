from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    source_store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    destination_store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False) # TRANSFER, DISCOUNT, BUNDLE, FEFO, PROCURE_LESS
    expected_value = Column(Float, default=0.0)
    estimated_cost = Column(Float, default=0.0)
    distance_km = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    reason = Column(String(500), nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, APPROVED, REJECTED, COMPLETED

    product = relationship("Product", back_populates="recommendations")
    batch = relationship("Batch", back_populates="recommendations")
    source_store = relationship("Store", foreign_keys=[source_store_id])
    destination_store = relationship("Store", foreign_keys=[destination_store_id])
    actions = relationship("Action", back_populates="recommendation", cascade="all, delete-orphan")
