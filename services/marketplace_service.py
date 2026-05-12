"""
Marketplace entegrasyon servisi.

Gerçek Trendyol / Hepsiburada API'leri kapalı/kısıtlı olduğundan
bu modül, aynı HTTP kontratını taklit eden mock fonksiyonlar içerir.
Gerçek API anahtarları geldiğinde sadece _fetch_* fonksiyonlarını
değiştirmek yeterli olacaktır — geri kalan iş akışı aynı kalır.
"""

from __future__ import annotations

import logging
import random
import string
from contextlib import contextmanager
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import text

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product

logger = logging.getLogger(__name__)

CHANNEL_TRENDYOL = "trendyol"
CHANNEL_HEPSIBURADA = "hepsiburada"
CHANNEL_DIRECT = "direct"

CHANNEL_LABELS = {
    CHANNEL_TRENDYOL: "Trendyol",
    CHANNEL_HEPSIBURADA: "Hepsiburada",
    CHANNEL_DIRECT: "Direkt",
}

@contextmanager
def _session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_channel_column() -> None:
    with _session_scope() as db:
        db.execute(text(
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS channel VARCHAR DEFAULT 'direct'"
        ))
        db.execute(text(
            "UPDATE orders SET channel = 'direct' WHERE channel IS NULL"
        ))


def _random_marketplace_id(prefix: str) -> str:
    suffix = "".join(random.choices(string.digits, k=9))
    return f"{prefix}-{suffix}"


def _fetch_trendyol_orders(limit: int = 5) -> list[dict]:
    sample_names = [
        "Ahmet Yılmaz", "Fatma Demir", "Mehmet Kaya",
        "Ayşe Şahin", "Ali Öztürk", "Zeynep Arslan",
    ]
    sample_products = [
        ("Organik Zeytinyağı 1L", 189.90),
        ("Çiçek Balı 500g", 129.50),
        ("Tam Buğday Unu 2kg", 49.90),
        ("Organik Domates 1kg", 34.90),
        ("Kuru İncir 250g", 79.90),
    ]
    orders = []
    for _ in range(random.randint(2, limit)):
        product_name, price = random.choice(sample_products)
        qty = random.randint(1, 3)
        orders.append({
            "marketplace_order_id": _random_marketplace_id("TY"),
            "customer_name": random.choice(sample_names),
            "customer_phone": f"05{random.randint(300000000, 399999999)}",
            "product_name": product_name,
            "quantity": qty,
            "unit_price": price,
            "total_amount": round(price * qty, 2),
            "channel": CHANNEL_TRENDYOL,
        })
    return orders


def _fetch_hepsiburada_orders(limit: int = 5) -> list[dict]:
    sample_names = [
        "Burak Çelik", "Selin Aydın", "Osman Koç",
        "Elif Yıldız", "Hasan Güneş", "Merve Doğan",
    ]
    sample_products = [
        ("Organik Zeytinyağı 1L", 189.90),
        ("Çiçek Balı 500g", 129.50),
        ("Fındık Ezmesi 300g", 94.90),
        ("Organik Mercimek 1kg", 44.90),
        ("Tahin 400g", 69.90),
    ]
    orders = []
    for _ in range(random.randint(1, limit)):
        product_name, price = random.choice(sample_products)
        qty = random.randint(1, 2)
        orders.append({
            "marketplace_order_id": _random_marketplace_id("HB"),
            "customer_name": random.choice(sample_names),
            "customer_phone": f"05{random.randint(400000000, 499999999)}",
            "product_name": product_name,
            "quantity": qty,
            "unit_price": price,
            "total_amount": round(price * qty, 2),
            "channel": CHANNEL_HEPSIBURADA,
        })
    return orders


def _get_or_create_customer(db, name: str, phone: str) -> Customer:
    customer = db.query(Customer).filter(Customer.full_name == name).first()
    if not customer:
        customer = Customer(
            full_name=name,
            phone=phone,
            address="Marketplace siparişi",
        )
        db.add(customer)
        db.flush()
    return customer


def _get_product_by_name(db, name: str) -> Product | None:
    product = db.query(Product).filter(Product.name == name).first()
    if not product:
        product = db.query(Product).filter(
            Product.name.ilike(f"%{name.split()[0]}%")
        ).first()
    return product


def _write_marketplace_orders(raw_orders: list[dict]) -> dict[str, Any]:
    ensure_channel_column()
    imported = []
    skipped = []

    with _session_scope() as db:
        for raw in raw_orders:
            marketplace_id = raw["marketplace_order_id"]
            channel = raw["channel"]

            existing = db.query(Order).filter(
                Order.order_number == marketplace_id
            ).first()
            if existing:
                skipped.append(marketplace_id)
                continue

            customer = _get_or_create_customer(db, raw["customer_name"], raw["customer_phone"])
            product = _get_product_by_name(db, raw["product_name"])

            order = Order(
                customer_id=customer.id,
                status="pending",
                total_amount=raw["total_amount"],
                created_at=datetime.now(UTC),
                order_number=marketplace_id,
                channel=channel,
            )
            db.add(order)
            db.flush()

            if product:
                db.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=raw["quantity"],
                    unit_price=raw["unit_price"],
                ))
                current = int(product.stock_quantity or 0)
                product.stock_quantity = max(0, current - raw["quantity"])
                if product.stock_quantity == 0:
                    order.notes = f"⚠️ {product.name} stoğu tükendi — marketplace pasife alınmalı"

            imported.append({
                "order_number": marketplace_id,
                "customer_name": raw["customer_name"],
                "product_name": raw["product_name"],
                "quantity": raw["quantity"],
                "total_amount": raw["total_amount"],
                "channel": channel,
                "stock_warning": product is not None and (product.stock_quantity or 0) == 0,
            })

    return {"imported": imported, "skipped": skipped}


def sync_trendyol_orders() -> dict[str, Any]:
    try:
        raw = _fetch_trendyol_orders()
        result = _write_marketplace_orders(raw)
        return {
            "success": True,
            "channel": CHANNEL_TRENDYOL,
            "imported_count": len(result["imported"]),
            "skipped_count": len(result["skipped"]),
            "orders": result["imported"],
        }
    except Exception as exc:
        logger.exception("Trendyol sync failed")
        return {"success": False, "message": str(exc)}


def sync_hepsiburada_orders() -> dict[str, Any]:
    try:
        raw = _fetch_hepsiburada_orders()
        result = _write_marketplace_orders(raw)
        return {
            "success": True,
            "channel": CHANNEL_HEPSIBURADA,
            "imported_count": len(result["imported"]),
            "skipped_count": len(result["skipped"]),
            "orders": result["imported"],
        }
    except Exception as exc:
        logger.exception("Hepsiburada sync failed")
        return {"success": False, "message": str(exc)}


def get_channel_report() -> dict[str, Any]:
    ensure_channel_column()
    try:
        with _session_scope() as db:
            from datetime import date
            today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=UTC)
            rows = db.execute(text("""
                SELECT
                    COALESCE(channel, 'direct') AS channel,
                    COUNT(*) AS order_count,
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM orders
                WHERE created_at >= :today
                GROUP BY COALESCE(channel, 'direct')
            """), {"today": today_start}).fetchall()

            channels = {}
            total_orders = 0
            total_revenue = 0.0
            for row in rows:
                ch = row[0]
                cnt = int(row[1])
                rev = float(row[2])
                channels[ch] = {"order_count": cnt, "revenue": rev}
                total_orders += cnt
                total_revenue += rev

            return {
                "success": True,
                "date": date.today().isoformat(),
                "channels": channels,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
            }
    except Exception as exc:
        logger.exception("Channel report failed")
        return {"success": False, "message": str(exc)}


def get_zero_stock_marketplace_warnings() -> list[str]:
    try:
        with _session_scope() as db:
            products = db.query(Product).filter(Product.stock_quantity == 0).all()
            return [p.name for p in products]
    except Exception:
        logger.exception("Zero stock check failed")
        return []