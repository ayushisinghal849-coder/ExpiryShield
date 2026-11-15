from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    quantity_sold = Column(Integer, default=0, nullable=False)
    sale_date = Column(Date, nullable=False, index=True)

    product = relationship("Product", back_populates="sales")
    store = relationship("Store", back_populates="sales")
