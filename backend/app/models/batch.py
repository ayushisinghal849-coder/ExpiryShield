from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    batch_code = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    received_date = Column(Date, nullable=True)

    product = relationship("Product", back_populates="batches")
    store = relationship("Store", back_populates="batches")
    recommendations = relationship("Recommendation", back_populates="batch", cascade="all, delete-orphan")
