from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)

    phone = Column(String)

    address = Column(String)

    orders = relationship("Order", back_populates="customer")