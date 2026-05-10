from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

from database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    price = Column(Float, nullable=False)

    stock_quantity = Column(Integer, default=0)

    order_items = relationship("OrderItem", back_populates="product")

    inventory_movements = relationship(
        "InventoryMovement",
        back_populates="product"
    )