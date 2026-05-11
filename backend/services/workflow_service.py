import logging
from datetime import date
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models.customer import Customer, CustomerRole
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product
from telegram_whatsapp_bot.order_formatter import format_warehouse_report, format_courier_report
import asyncio
import os
from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id: int, text: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment")
        return
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"Failed to send telegram message to {chat_id}: {e}")

def get_todays_orders_data(db: Session):
    # Bugünün siparişlerini ve detaylarını çekiyoruz
    rows = (
        db.query(Order, Customer)
        .join(Customer, Customer.id == Order.customer_id)
        .filter(Order.created_at >= date.today())
        .filter(Order.status != "cancelled")
        .all()
    )
    
    orders_data = []
    for order, customer in rows:
        # Her siparişin ürünlerini bul
        items = db.query(OrderItem, Product).join(Product, Product.id == OrderItem.product_id).filter(OrderItem.order_id == order.id).all()
        for item, product in items:
            orders_data.append({
                "order_number": order.order_number or f"ORD-{order.id:06d}",
                "customer_name": customer.full_name,
                "address": customer.address,
                "product_name": product.name,
                "quantity": item.quantity
            })
    return orders_data

async def run_daily_workflow():
    """
    Her sabah çalışan ana iş akışı.
    Depo sorumlularına hazırlık listesi, kuryelere teslimat rotası gönderir.
    """
    db = SessionLocal()
    try:
        orders_data = get_todays_orders_data(db)
        
        # 1. Depo Sorumlularını Bul (cooperative rolü)
        warehouse_users = db.query(Customer).filter(Customer.role == CustomerRole.cooperative).filter(Customer.telegram_user_id.isnot(None)).all()
        warehouse_text = format_warehouse_report(orders_data)
        
        for user in warehouse_users:
            await send_telegram_message(user.telegram_user_id, warehouse_text)
            
        # 2. Kuryeleri/Satıcıları Bul (seller rolü)
        courier_users = db.query(Customer).filter(Customer.role == CustomerRole.seller).filter(Customer.telegram_user_id.isnot(None)).all()
        courier_text = format_courier_report(orders_data)
        
        for user in courier_users:
            await send_telegram_message(user.telegram_user_id, courier_text)
            
        logger.info(f"Daily workflow completed. Sent to {len(warehouse_users)} warehouse and {len(courier_users)} courier users.")
    finally:
        db.close()

def start_workflow_task():
    # APScheduler asenkron fonksiyonları doğrudan çalıştıramaz, bu yüzden asyncio ile sarmalıyoruz
    asyncio.run(run_daily_workflow())
