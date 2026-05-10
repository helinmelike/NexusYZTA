"""Compatibility wrapper for support ticket operations."""

from typing import Any

from services.support_ticket_service import (
    create_support_ticket as _create_support_ticket,
    get_customer_tickets as _get_customer_tickets,
    update_ticket_status as _update_ticket_status,
)


def create_support_ticket(
    customer_id: int,
    subject: str,
    message: str,
    telegram_user_id: int | None = None,
) -> dict[str, Any]:
    """Backward-compatible create with optional telegram_user_id."""
    _ = subject
    if telegram_user_id is None:
        return {
            "success": False,
            "message": "telegram_user_id gerekli.",
            "data": None,
        }
    return _create_support_ticket(
        customer_id=customer_id,
        telegram_user_id=telegram_user_id,
        message=message,
    )


def list_customer_tickets(customer_id: int, telegram_user_id: int | None = None) -> dict[str, Any]:
    return _get_customer_tickets(customer_id=customer_id, telegram_user_id=telegram_user_id)


def close_ticket(ticket_id: int, customer_id: int | None = None, telegram_user_id: int | None = None) -> dict[str, Any]:
    return _update_ticket_status(
        ticket_id=ticket_id,
        status="resolved",
        customer_id=customer_id,
        telegram_user_id=telegram_user_id,
    )
