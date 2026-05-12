from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database.base import Base
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    status = Column(String, default='pending')
    channel = Column(String, default='direct')
    total_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship('Customer', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')
