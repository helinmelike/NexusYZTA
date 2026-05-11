from __future__ import annotations

import re
from typing import Any

from database.db import SessionLocal
from database.models.order import Order

_ORDER_NUMBER_RE = re.compile(r"\bORD-(\d{6,})\b", re.IGNORECASE)
_ORDER_ID_RE = re.compile(r"(?:sipari(?:\u015f|s))\s*#?\s*(\d+)", re.IGNORECASE)


def format_order_success(order: dict[str, Any], product_name: str, quantity: int) -> str:
    order_number = str(order.get("order_number") or "").strip()
    if not order_number:
        order_id = order.get("order_id") or order.get("id")
        order_number = f"ORD-{int(order_id):06d}" if order_id is not None else "-"
    return (
        "✅ <b>Siparişiniz Başarıyla Oluşturuldu!</b>\n\n"
        "📦 Sipariş Numarası:\n"
        f"<code>{order_number}</code>\n\n"
        "🛒 Ürün:\n"
        f"{product_name}\n\n"
        "⚖️ Miktar:\n"
        f"{int(quantity)} adet\n\n"
        "🌐 Detaylı işlemler için web panelini kullanabilirsiniz.\n\n"
        "🔗 Detaylı bilgi:\n"
        "https://example.com"
    )


def resolve_order_id_from_text(text: str) -> int | None:
    raw = (text or "").strip()
    if not raw:
        return None

    order_number_match = _ORDER_NUMBER_RE.search(raw)
    if order_number_match:
        order_number = f"ORD-{order_number_match.group(1)}"
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_number == order_number).first()
            return int(order.id) if order else None
        finally:
            db.close()

    order_id_match = _ORDER_ID_RE.search(raw)
    if order_id_match:
        return int(order_id_match.group(1))

    any_number_match = re.search(r"\b(\d+)\b", raw)
    if any_number_match:
        return int(any_number_match.group(1))

    if raw.isdigit():
        return int(raw)

    return None
