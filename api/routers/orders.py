from fastapi import APIRouter
from services.order_service import list_recent_orders, get_order_detail, cancel_order
from services.cargo_service import update_cargo_status

router = APIRouter()

@router.get("/")
def list_orders():
    return list_recent_orders(50, include_items=True)

@router.get("/{order_id}")
def get_order(order_id: int):
    return get_order_detail(order_id)

@router.patch("/{order_id}/status")
def update_order(order_id: int, body: dict):
    return update_cargo_status(order_id, body.get("new_status", ""))

@router.delete("/{order_id}")
def cancel(order_id: int):
    return cancel_order(order_id)