from fastapi import Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from repositories.order_repository import OrderRepository
from services import cargo_service 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)

from services import cargo_service

def get_cargo_service():
    return cargo_service