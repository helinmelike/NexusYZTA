from fastapi import APIRouter
from services.customer_service import get_customer, find_customer_by_phone, create_customer, customer_statistics

router = APIRouter()

@router.get("/")
def list_customers():
    from database.db import SessionLocal
    from database.models.customer import Customer
    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        return {"success": True, "data": [{"id": c.id, "full_name": c.full_name, "phone": c.phone, "address": c.address} for c in customers]}
    finally:
        db.close()

@router.get("/{customer_id}")
def get_customer_by_id(customer_id: int):
    return get_customer(customer_id)

@router.get("/phone/{phone}")
def find_by_phone(phone: str):
    return find_customer_by_phone(phone)

@router.get("/{customer_id}/stats")
def stats(customer_id: int):
    return customer_statistics(customer_id)