"""Support ticket service layer."""

from __future__ import annotations

import logging
from typing import Any

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.support_ticket import SupportTicket

logger = logging.getLogger(__name__)

STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_RESOLVED = "resolved"
ALLOWED_STATUSES = {STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED}


def _serialize_ticket(ticket: SupportTicket) -> dict[str, Any]:
    return {
        "id": ticket.id,
        "customer_id": ticket.customer_id,
        "telegram_user_id": ticket.telegram_user_id,
        "message": ticket.message,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


def create_support_ticket(customer_id: int, telegram_user_id: int, message: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        clean_message = (message or "").strip()
        if not clean_message:
            logger.warning("support_ticket.create.validation_failed empty message customer_id=%s", customer_id)
            return {"success": False, "message": "Mesaj boş olamaz.", "data": None}

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            logger.warning("support_ticket.create.customer_not_found customer_id=%s", customer_id)
            return {"success": False, "message": "Müşteri bulunamadı.", "data": None}

        if customer.telegram_user_id and int(customer.telegram_user_id) != int(telegram_user_id):
            logger.warning(
                "support_ticket.create.telegram_mismatch customer_id=%s customer_tg=%s request_tg=%s",
                customer_id,
                customer.telegram_user_id,
                telegram_user_id,
            )
            return {"success": False, "message": "Müşteri kimliği doğrulanamadı.", "data": None}

        ticket = SupportTicket(
            customer_id=customer_id,
            telegram_user_id=telegram_user_id,
            message=clean_message,
            status=STATUS_OPEN,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        logger.info("support_ticket.create.success ticket_id=%s customer_id=%s", ticket.id, customer_id)
        return {"success": True, "message": "Destek talebi oluşturuldu.", "data": _serialize_ticket(ticket)}
    except Exception:
        db.rollback()
        logger.exception("support_ticket.create.exception customer_id=%s", customer_id)
        return {"success": False, "message": "Destek talebi oluşturulamadı.", "data": None}
    finally:
        db.close()


def get_customer_tickets(customer_id: int, telegram_user_id: int | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id)
        if telegram_user_id is not None:
            query = query.filter(SupportTicket.telegram_user_id == telegram_user_id)
        tickets = query.order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc()).all()
        logger.info("support_ticket.list.success customer_id=%s count=%s", customer_id, len(tickets))
        return {
            "success": True,
            "message": "Ticketlar listelendi.",
            "data": [_serialize_ticket(ticket) for ticket in tickets],
        }
    except Exception:
        db.rollback()
        logger.exception("support_ticket.list.exception customer_id=%s", customer_id)
        return {"success": False, "message": "Ticketlar listelenemedi.", "data": []}
    finally:
        db.close()


def get_ticket_by_id(ticket_id: int, customer_id: int, telegram_user_id: int | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not ticket:
            logger.warning("support_ticket.get.not_found ticket_id=%s", ticket_id)
            return {"success": False, "message": "Ticket bulunamadı.", "data": None}

        if ticket.customer_id != customer_id:
            logger.warning(
                "support_ticket.get.unauthorized ticket_id=%s ticket_customer=%s request_customer=%s",
                ticket_id,
                ticket.customer_id,
                customer_id,
            )
            return {"success": False, "message": "Bu ticketa erişim yetkiniz yok.", "data": None}

        if telegram_user_id is not None and ticket.telegram_user_id != telegram_user_id:
            logger.warning(
                "support_ticket.get.telegram_mismatch ticket_id=%s ticket_tg=%s request_tg=%s",
                ticket_id,
                ticket.telegram_user_id,
                telegram_user_id,
            )
            return {"success": False, "message": "Bu ticketa erişim yetkiniz yok.", "data": None}

        logger.info("support_ticket.get.success ticket_id=%s customer_id=%s", ticket_id, customer_id)
        return {"success": True, "message": "Ticket bulundu.", "data": _serialize_ticket(ticket)}
    except Exception:
        db.rollback()
        logger.exception("support_ticket.get.exception ticket_id=%s customer_id=%s", ticket_id, customer_id)
        return {"success": False, "message": "Ticket bilgisi alınamadı.", "data": None}
    finally:
        db.close()


def list_all_open_tickets(status: str | None = None) -> dict[str, Any]:
    """
    Admin dashboard için tüm ticketları listeler.
    status filtresi: 'open', 'in_progress', 'resolved' veya None (hepsi)
    """
    db = SessionLocal()
    try:
        query = (
            db.query(SupportTicket, Customer)
            .join(Customer, Customer.id == SupportTicket.customer_id)
            .order_by(SupportTicket.created_at.desc())
        )
        if status:
            query = query.filter(SupportTicket.status == status)

        rows = query.limit(100).all()

        data = []
        for ticket, customer in rows:
            entry = _serialize_ticket(ticket)
            entry["customer_name"] = customer.full_name if customer else "Bilinmiyor"
            entry["customer_phone"] = customer.phone if customer else None
            msg = ticket.message or ""
            if "iade" in msg.lower():
                entry["topic"] = "İade"
            elif "iptal" in msg.lower():
                entry["topic"] = "İptal"
            elif "destek" in msg.lower() or "escalation" in msg.lower():
                entry["topic"] = "Destek"
            elif "kargo" in msg.lower() or "gecik" in msg.lower():
                entry["topic"] = "Kargo"
            else:
                entry["topic"] = "Diğer"
            data.append(entry)

        return {"success": True, "message": "Ticketlar listelendi.", "data": data}
    except Exception:
        db.rollback()
        logger.exception("support_ticket.list_all.exception")
        return {"success": False, "message": "Ticketlar listelenemedi.", "data": []}
    finally:
        db.close()


def admin_resolve_ticket(ticket_id: int) -> dict[str, Any]:
    """Admin panelden ticket'ı çözüldü olarak işaretle."""
    return update_ticket_status(ticket_id=ticket_id, status=STATUS_RESOLVED)


def update_ticket_status(
    ticket_id: int,
    status: str,
    customer_id: int | None = None,
    telegram_user_id: int | None = None,
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        normalized_status = (status or "").strip().lower()
        if normalized_status not in ALLOWED_STATUSES:
            logger.warning("support_ticket.update.invalid_status ticket_id=%s status=%s", ticket_id, status)
            return {"success": False, "message": "Geçersiz ticket durumu.", "data": None}

        ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not ticket:
            logger.warning("support_ticket.update.not_found ticket_id=%s", ticket_id)
            return {"success": False, "message": "Ticket bulunamadı.", "data": None}

        if customer_id is not None and ticket.customer_id != customer_id:
            logger.warning(
                "support_ticket.update.unauthorized ticket_id=%s ticket_customer=%s request_customer=%s",
                ticket_id,
                ticket.customer_id,
                customer_id,
            )
            return {"success": False, "message": "Bu ticketı güncelleme yetkiniz yok.", "data": None}

        if telegram_user_id is not None and ticket.telegram_user_id != telegram_user_id:
            logger.warning(
                "support_ticket.update.telegram_mismatch ticket_id=%s ticket_tg=%s request_tg=%s",
                ticket_id,
                ticket.telegram_user_id,
                telegram_user_id,
            )
            return {"success": False, "message": "Bu ticketı güncelleme yetkiniz yok.", "data": None}

        ticket.status = normalized_status
        db.commit()
        db.refresh(ticket)
        logger.info("support_ticket.update.success ticket_id=%s status=%s", ticket_id, normalized_status)
        return {"success": True, "message": "Ticket durumu güncellendi.", "data": _serialize_ticket(ticket)}
    except Exception:
        db.rollback()
        logger.exception("support_ticket.update.exception ticket_id=%s", ticket_id)
        return {"success": False, "message": "Ticket durumu güncellenemedi.", "data": None}
    finally:
        db.close()