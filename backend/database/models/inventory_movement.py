from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"))

    movement_type = Column(String, nullable=False)

    quantity = Column(Integer, nullable=False)

    note = Column(String)

    product = relationship(
        "Product",
        back_populates="inventory_movements"
    )