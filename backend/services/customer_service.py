"""Customer service layer."""

from contextlib import contextmanager
from typing import Any

from sqlalchemy import func

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.order import Order


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


def _serialize_customer(customer: Customer) -> dict[str, Any]:
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "address": customer.address,
    }


def get_customer(customer_id: int) -> dict[str, Any]:
    """Get customer by id."""
    with _session_scope() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "Customer not found", "data": None}
        return {"success": True, "message": "Customer fetched", "data": _serialize_customer(customer)}


def find_customer_by_phone(phone: str) -> dict[str, Any]:
    """Find customer by phone number."""
    with _session_scope() as db:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not customer:
            return {"success": False, "message": "Customer not found", "data": None}
        return {"success": True, "message": "Customer fetched", "data": _serialize_customer(customer)}


def create_customer(full_name: str, phone: str, address: str) -> dict[str, Any]:
    """Create a new customer if phone is not already registered."""
    with _session_scope() as db:
        existing = db.query(Customer).filter(Customer.phone == phone).first()
        if existing:
            return {
                "success": False,
                "message": "Phone already registered",
                "data": _serialize_customer(existing),
            }

        customer = Customer(full_name=full_name, phone=phone, address=address)
        db.add(customer)
        db.flush()
        db.refresh(customer)
        return {"success": True, "message": "Customer created", "data": _serialize_customer(customer)}


def customer_statistics(customer_id: int) -> dict[str, Any]:
    """Return order statistics of a customer."""
    with _session_scope() as db:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "Customer not found", "data": None}

        total_orders = db.query(func.count(Order.id)).filter(Order.customer_id == customer_id).scalar() or 0
        total_spent = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.customer_id == customer_id).scalar() or 0
        shipped_count = (
            db.query(func.count(Order.id))
            .filter(Order.customer_id == customer_id, Order.status == "shipped")
            .scalar()
            or 0
        )
        pending_count = (
            db.query(func.count(Order.id))
            .filter(Order.customer_id == customer_id, Order.status == "pending")
            .scalar()
            or 0
        )

        return {
            "success": True,
            "message": "Customer statistics fetched",
            "data": {
                "customer": _serialize_customer(customer),
                "total_orders": int(total_orders),
                "total_spent": float(total_spent),
                "status_breakdown": {
                    "shipped": int(shipped_count),
                    "pending": int(pending_count),
                },
            },
        }
