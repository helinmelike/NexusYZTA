from pydantic import BaseModel, Field


class PriceFeedbackRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    suggested_price: float = Field(..., gt=0)
    accepted: bool
    strategy: str
    final_price: float | None = Field(default=None, gt=0)
