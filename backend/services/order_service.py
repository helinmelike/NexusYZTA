"""Order service layer for database-backed order operations."""

from contextlib import contextmanager
from datetime import datetime, UTC
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product

logger = logging.getLogger(__name__)


@contextmanager
def _session_scope():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _serialize_order(order: Order, include_items: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "customer_name": order.customer.full_name if order.customer else None,
        "status": order.status,
        "total_amount": float(order.total_amount or 0),
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
    if include_items:
        payload["items"] = [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else None,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "line_total": float(item.quantity * item.unit_price),
            }
            for item in order.items
        ]
    return payload


def _ensure_order_schema(db: Session) -> None:
    columns = {
        row[1]
        for row in db.execute(text("PRAGMA table_info(orders)")).fetchall()
    }
    if "order_number" not in columns:
        db.execute(text("ALTER TABLE orders ADD COLUMN order_number VARCHAR"))
        db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_order_number ON orders (order_number)"))
    if "created_at" not in columns:
        db.execute(text("ALTER TABLE orders ADD COLUMN created_at DATETIME"))
        db.execute(text("UPDATE orders SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))


def create_order(customer_name: str, product_name: str) -> dict[str, Any]:
    """
    Backward-compatible helper used by Telegram bot.

    Creates a simple order with quantity=1 for the given customer and product.
    If customer does not exist, it will be created with a placeholder phone.
    """
    db = SessionLocal()
    try:
        _ensure_order_schema(db)

        customer = db.query(Customer).filter(Customer.full_name == customer_name).first()
        if not customer:
            customer = Customer(
                full_name=customer_name,
                phone=f"auto-{customer_name.lower().replace(' ', '-')}",
                address="Adres belirtilmedi",
            )
            db.add(customer)
            db.flush()

        product = db.query(Product).filter(Product.name == product_name).first()
        if not product:
            return {"success": False, "message": "Product not found", "data": None}

        if (product.stock_quantity or 0) < 1:
            return {"success": False, "message": "Insufficient stock", "data": None}

        order = Order(
            customer_id=customer.id,
            status="pending",
            total_amount=float(product.price),
            created_at=datetime.now(UTC),
        )
        logger.info("[ORDER_DEBUG] Order object created")
        db.add(order)
        logger.info("[ORDER_DEBUG] Order added to session")
        db.flush()

        order.order_number = f"ORD-{order.id:06d}"

        item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=float(product.price))
        db.add(item)
        product.stock_quantity = int(product.stock_quantity or 0) - 1

        db.commit()
        logger.info("[ORDER_DEBUG] Commit success")
        db.refresh(order)
        logger.info("[ORDER_DEBUG] Order ID = %s", order.id)

        return {
            "success": True,
            "message": "Order created",
            "data": {
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_id": order.customer_id,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            },
        }
    except Exception as exc:
        db.rollback()
        logger.exception("[ORDER_DEBUG] Order create failed before commit: %s", exc)
        return {"success": False, "message": "Order persistence failed", "data": None}
    finally:
        db.close()


def get_order_by_id(order_id: int) -> dict[str, Any]:
    """Return basic order data by order id."""
    with _session_scope() as db:
        _ensure_order_schema(db)
        order = (
            db.query(Order)
            .options(joinedload(Order.customer))
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            return {"success": False, "message": "Order not found", "data": None}
        return {"success": True, "message": "Order fetched", "data": _serialize_order(order)}


def get_customer_orders(customer_id: int) -> dict[str, Any]:
    """List all orders of a given customer."""
    with _session_scope() as db:
        _ensure_order_schema(db)
        orders = (
            db.query(Order)
            .options(joinedload(Order.customer))
            .filter(Order.customer_id == customer_id)
            .order_by(Order.id.desc())
            .all()
        )
        data = [_serialize_order(order) for order in orders]
        return {"success": True, "message": "Customer orders fetched", "data": data}


def cancel_order(order_id: int) -> dict[str, Any]:
    """Cancel order if not already shipped."""
    with _session_scope() as db:
        _ensure_order_schema(db)
        order = (
            db.query(Order)
            .options(joinedload(Order.items).joinedload(OrderItem.product))
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            return {"success": False, "message": "Order not found", "data": None}

        if order.status == "shipped":
            return {"success": False, "message": "Shipped order cannot be cancelled", "data": None}

        for item in order.items:
            if item.product:
                item.product.stock_quantity = int(item.product.stock_quantity or 0) + int(item.quantity)

        order.status = "cancelled"
        return {"success": True, "message": "Order cancelled", "data": _serialize_order(order)}


def list_recent_orders(limit: int = 10) -> dict[str, Any]:
    """List most recent orders."""
    safe_limit = max(1, min(int(limit), 100))
    with _session_scope() as db:
        _ensure_order_schema(db)
        orders = (
            db.query(Order)
            .options(joinedload(Order.customer))
            .order_by(Order.id.desc())
            .limit(safe_limit)
            .all()
        )
        data = [_serialize_order(order) for order in orders]
        return {"success": True, "message": "Recent orders fetched", "data": data}


def get_order_detail(order_id: int) -> dict[str, Any]:
    """Return detailed order payload with nested items."""
    with _session_scope() as db:
        _ensure_order_schema(db)
        order = (
            db.query(Order)
            .options(
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.product),
            )
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            return {"success": False, "message": "Order not found", "data": None}
        return {
            "success": True,
            "message": "Order detail fetched",
            "data": _serialize_order(order, include_items=True),
        }
