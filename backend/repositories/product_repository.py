from sqlalchemy.orm import Session

from database.models.product import Product
from repositories.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(Product, db)
