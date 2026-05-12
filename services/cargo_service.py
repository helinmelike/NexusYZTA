"""Cargo service layer backed by order status."""

from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any

from database.db import SessionLocal
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


_CARGO_STATUS_BY_ORDER_STATUS = {
    "pending": "label_created",
    "preparing": "in_preparation",
    "shipped": "in_transit",
    "delivered": "delivered",
    "cancelled": "cancelled",
}


def _tracking_number_from_order_id(order_id: int) -> str:
    return f"ORD-{int(order_id):06d}"


def _order_id_from_tracking_number(tracking_number: str) -> int | None:
    if not isinstance(tracking_number, str):
        return None
    if not tracking_number.startswith("ORD-"):
        return None
    raw = tracking_number.replace("ORD-", "")
    return int(raw) if raw.isdigit() else None


def get_cargo_status(order_id: int) -> dict[str, Any]:
    """Get cargo status by order id."""
    with _session_scope() as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "message": "Order not found", "data": None}
        cargo_status = _CARGO_STATUS_BY_ORDER_STATUS.get(order.status, "unknown")
        return {
            "success": True,
            "message": "Cargo status fetched",
            "data": {
                "order_id": order.id,
                "tracking_number": _tracking_number_from_order_id(order.id),
                "order_status": order.status,
                "cargo_status": cargo_status,
            },
        }


def track_cargo(tracking_number: str) -> dict[str, Any]:
    """Track cargo via synthetic tracking number mapped to order id."""
    order_id = _order_id_from_tracking_number(tracking_number)
    if not order_id:
        return {"success": False, "message": "Invalid tracking number format", "data": None}
    return get_cargo_status(order_id)


def get_estimated_delivery(tracking_number: str) -> dict[str, Any]:
    """Estimate delivery date based on current order status."""
    track_result = track_cargo(tracking_number)
    if not track_result["success"]:
        return track_result

    cargo_status = track_result["data"]["cargo_status"]
    today = date.today()
    if cargo_status == "label_created":
        eta = today + timedelta(days=4)
    elif cargo_status == "in_preparation":
        eta = today + timedelta(days=3)
    elif cargo_status == "in_transit":
        eta = today + timedelta(days=1)
    elif cargo_status == "delivered":
        eta = today
    else:
        eta = today + timedelta(days=5)

    return {
        "success": True,
        "message": "Estimated delivery calculated",
        "data": {
            **track_result["data"],
            "estimated_delivery_date": eta.isoformat(),
        },
    }


def update_cargo_status(order_id: int, new_status: str) -> dict[str, Any]:
    """
    Update order status through cargo workflow.

    Allowed statuses: pending, preparing, shipped, delivered, cancelled.
    """
    allowed = {"pending", "preparing", "shipped", "delivered", "cancelled"}
    if new_status not in allowed:
        return {"success": False, "message": "Invalid status", "data": {"allowed_statuses": sorted(allowed)}}

    with _session_scope() as db:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "message": "Order not found", "data": None}

        order.status = new_status
        return {
            "success": True,
            "message": "Cargo status updated",
            "data": {
                "order_id": order.id,
                "tracking_number": _tracking_number_from_order_id(order.id),
                "order_status": order.status,
                "cargo_status": _CARGO_STATUS_BY_ORDER_STATUS.get(order.status, "unknown"),
            },
        }
