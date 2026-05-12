from pydantic import BaseModel


class OrderCreateRequest(BaseModel):
    customer_id: int
    total_amount: float = 0.0


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: float

    class Config:
        from_attributes = True
