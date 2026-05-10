from database.db import SessionLocal
from database.models.customer import Customer


def get_customer_by_telegram_id(telegram_user_id: int):
    db = SessionLocal()
    try:
        return (
            db.query(Customer)
            .filter(Customer.telegram_user_id == telegram_user_id)
            .first()
        )
    finally:
        db.close()


def create_customer_from_telegram(user):
    db = SessionLocal()
    try:
        customer = Customer(
            full_name=user.full_name or user.first_name or "Telegram User",
            telegram_user_id=user.id,
            phone=None,
            address="Adres belirtilmedi",
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    finally:
        db.close()


def get_or_create_customer_from_telegram(user):
    customer = get_customer_by_telegram_id(user.id)

    if customer:
        return customer

    return create_customer_from_telegram(user)