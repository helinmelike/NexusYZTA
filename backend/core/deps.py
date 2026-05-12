from fastapi import Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal
from repositories.order_repository import OrderRepository
from services import cargo_service
from services.ml.ml_service import MLService
from repositories.product_repository import ProductRepository

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)

def get_cargo_service():
    return cargo_service

def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)

def get_ml_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    product_repo: ProductRepository = Depends(get_product_repository),
) -> MLService:
    from services.ml.ml_service import MLService
    return MLService(repo=order_repo, product_repo=product_repo)