from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id"))

    status = Column(String, default="pending")

    total_amount = Column(Float, default=0)

    customer = relationship("Customer", back_populates="orders")

    items = relationship("OrderItem", back_populates="order")