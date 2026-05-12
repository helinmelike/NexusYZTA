"""Gelen mesaj? i?leme katman?."""

from __future__ import annotations

from channels.instagram.message_reader import IncomingMessage
from services.cargo_service import CargoService
from services.order_service import OrderService
from services.support_service import SupportService


class MessageHandler:
    """Mesaj i?eri?ine g?re servis routing yapar."""

    def __init__(self) -> None:
        self.order_service = OrderService()
        self.cargo_service = CargoService()
        self.support_service = SupportService()

    def handle(self, incoming: IncomingMessage) -> str:
        text = incoming.text.lower()

        if "sipari?" in text or "siparis" in text:
            return self.order_service.handle_order_query(incoming.username, incoming.text)

        if "kargo" in text or "teslim" in text:
            return self.cargo_service.handle_cargo_query(incoming.username, incoming.text)

        return self.support_service.handle_support_query(incoming.username, incoming.text)
