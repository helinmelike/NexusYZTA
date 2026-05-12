from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database.base import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"))

    movement_type = Column(String, nullable=False)

    quantity = Column(Integer, nullable=False)

    note = Column(String)

    created_at    = Column(DateTime, default=datetime.utcnow)

    product = relationship(
        "Product",
        back_populates="inventory_movements"
    )