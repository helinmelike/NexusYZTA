from pydantic import BaseModel


class CargoStatusResponse(BaseModel):
    order_id: int
    tracking_number: str
    order_status: str
    cargo_status: str


class DelayedOrderResponse(CargoStatusResponse):
    eta: str
    days_late: int


class CargoStatusUpdateRequest(BaseModel):
    new_status: str


class DelayedOrdersListResponse(BaseModel):
    success: bool
    count: int
    data: list[DelayedOrderResponse]
