from database.db import SessionLocal
from database.models.customer import Customer


def get_customer_by_telegram_id(telegram_user_id: int):
    db = SessionLocal()

    customer = (
        db.query(Customer)
        .filter(Customer.telegram_user_id == telegram_user_id)
        .first()
    )

    db.close()

    return customer


def create_customer_from_telegram(user):
    db = SessionLocal()

    customer = Customer(
        name=user.first_name or "Telegram User",
        telegram_user_id=user.id,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()

    return customer


def get_or_create_customer_from_telegram(user):
    customer = get_customer_by_telegram_id(user.id)

    if customer:
        return customer

    return create_customer_from_telegram(user)