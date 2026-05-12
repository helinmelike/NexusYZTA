from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from database.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id"))

    status = Column(String, default="pending")

    total_amount = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    customer = relationship("Customer", back_populates="orders")

    items = relationship("OrderItem", back_populates="order")
