from pydantic import BaseModel


class CustomerCreateRequest(BaseModel):
    full_name: str
    phone: str | None = None
    address: str | None = None
    email: str | None = None


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    phone: str | None
    address: str | None

    class Config:
        from_attributes = True
