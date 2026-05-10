"""Support service layer.

Note:
This project currently has no support ticket model/table in database models.
Functions below return structured error payloads and keep interface stable
until a SupportTicket model is added.
"""

from typing import Any


def create_support_ticket(customer_id: int, subject: str, message: str) -> dict[str, Any]:
    """Create support ticket (blocked: missing SupportTicket model)."""
    return {
        "success": False,
        "message": "Support ticket feature is unavailable: SupportTicket model not found in database schema",
        "data": {
            "customer_id": customer_id,
            "subject": subject,
            "message": message,
        },
    }


def list_customer_tickets(customer_id: int) -> dict[str, Any]:
    """List support tickets (blocked: missing SupportTicket model)."""
    return {
        "success": False,
        "message": "Support ticket feature is unavailable: SupportTicket model not found in database schema",
        "data": {"customer_id": customer_id, "tickets": []},
    }


def close_ticket(ticket_id: int) -> dict[str, Any]:
    """Close support ticket (blocked: missing SupportTicket model)."""
    return {
        "success": False,
        "message": "Support ticket feature is unavailable: SupportTicket model not found in database schema",
        "data": {"ticket_id": ticket_id},
    }
