"""Order service layer for database-backed order operations."""

from contextlib import contextmanager
from typing import Any

from sqlalchemy.orm import Session, joinedload

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product


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
        "customer_id": order.customer_id,
        "customer_name": order.customer.full_name if order.customer else None,
        "status": order.status,
        "total_amount": float(order.total_amount or 0),
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


def create_order(customer_name: str, product_name: str) -> dict[str, Any]:
    """
    Backward-compatible helper used by Telegram bot.

    Creates a simple order with quantity=1 for the given customer and product.
    If customer does not exist, it will be created with a placeholder phone.
    """
    with _session_scope() as db:
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

        order = Order(customer_id=customer.id, status="pending", total_amount=float(product.price))
        db.add(order)
        db.flush()

        item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, unit_price=float(product.price))
        db.add(item)
        product.stock_quantity = int(product.stock_quantity or 0) - 1

        db.refresh(order)
        return {"success": True, "message": "Order created", "data": {"order_id": order.id}}


def get_order_by_id(order_id: int) -> dict[str, Any]:
    """Return basic order data by order id."""
    with _session_scope() as db:
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
