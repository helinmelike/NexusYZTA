from database.db import engine
from database.base import Base

from database.models.product import Product
from database.models.customer import Customer
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.inventory_movement import InventoryMovement
from database.models.support_ticket import SupportTicket

Base.metadata.create_all(bind=engine)

print("Database oluşturuldu.")