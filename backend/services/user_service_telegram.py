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


def resolve_and_link_customer_from_telegram(user):
    telegram_user_id = user.id
    full_name = user.full_name or user.first_name or ""

    db = SessionLocal()
    try:
        customer = (
            db.query(Customer)
            .filter(Customer.telegram_user_id == telegram_user_id)
            .first()
        )

        # Fallback with existing schema only: exact full_name match.
        if not customer and full_name:
            customer = (
                db.query(Customer)
                .filter(Customer.full_name == full_name)
                .first()
            )

        if not customer:
            return None

        # Prevent hijacking if a different Telegram id is already linked.
        if customer.telegram_user_id and int(customer.telegram_user_id) != int(telegram_user_id):
            return None

        customer.telegram_user_id = telegram_user_id
        if full_name:
            customer.full_name = full_name
        db.commit()
        db.refresh(customer)
        return customer
    finally:
        db.close()


# Backward-compatible alias used by telegram bot code.
def get_or_create_customer_from_telegram(user):
    return resolve_and_link_customer_from_telegram(user)

