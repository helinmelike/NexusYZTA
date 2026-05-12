from fastapi import APIRouter, Depends
from core.deps import get_cargo_service
from schemas.cargo import CargoStatusUpdateRequest
from services import cargo_service

router = APIRouter()

@router.get("/status/{order_id}")
def get_cargo_status(
    order_id: int,
    svc = Depends(get_cargo_service),
):
    return svc.get_cargo_status(order_id)

@router.get("/track/{tracking_number}")
def track_cargo(
    tracking_number: str,
    svc = Depends(get_cargo_service),
):
    return svc.track_cargo(tracking_number)

@router.get("/delivery/{tracking_number}")
def get_estimated_delivery(
    tracking_number: str,
    svc = Depends(get_cargo_service),
):
    return svc.get_estimated_delivery(tracking_number)

@router.patch("/{order_id}/status")
def update_cargo_status(
    order_id: int,
    body: CargoStatusUpdateRequest,
    svc = Depends(get_cargo_service),
):
    return svc.update_cargo_status(order_id, body.new_status)