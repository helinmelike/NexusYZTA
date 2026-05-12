from fastapi import APIRouter, Query
from services.support_ticket_service import list_all_open_tickets, admin_resolve_ticket

router = APIRouter()


@router.get("/")
def list_tickets(status: str | None = Query(default=None)):
    return list_all_open_tickets(status=status)


@router.patch("/{ticket_id}/resolve")
def resolve_ticket(ticket_id: int):
    return admin_resolve_ticket(ticket_id)