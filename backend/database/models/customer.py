import enum

from sqlalchemy import BigInteger, Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from database.base import Base


class CustomerRole(enum.Enum):
    customer = "customer"
    seller = "seller"
    cooperative = "cooperative"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    telegram_user_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone = Column(String)
    address = Column(String)
    role = Column(Enum(CustomerRole), default=CustomerRole.customer, nullable=False)

    orders = relationship("Order", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")