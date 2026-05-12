from sqlalchemy.orm import Session

from database.models.customer import Customer
from repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def get_by_phone(self, phone: str) -> Customer | None:
        return (
            self.db.query(Customer)
            .filter(Customer.phone == phone)
            .first()
        )
