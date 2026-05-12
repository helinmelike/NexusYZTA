from sqlalchemy.orm import Session

from database.models.order import Order
from repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def get_by_status(self, *statuses: str) -> list[Order]:
        return (
            self.db.query(Order)
            .filter(Order.status.in_(statuses))
            .all()
        )

    def update_status(self, order_id: int, new_status: str) -> Order | None:
        order = self.get_by_id(order_id)
        if order:
            order.status = new_status
            self.db.commit()
            self.db.refresh(order)
        return order
