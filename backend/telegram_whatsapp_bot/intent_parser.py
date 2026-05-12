from __future__ import annotations

import re

from telegram_whatsapp_bot.intent_types import IntentType, ParsedIntent


_TRACKING_RE = re.compile(r"\bORD-\d{6,}\b", re.IGNORECASE)
_ORDER_ID_RE = re.compile(r"(?:sipari(?:\u015f|s))\s*#?\s*(\d+)", re.IGNORECASE)
_ORDER_NUMBER_RE = re.compile(r"\bORD-\d{6,}\b", re.IGNORECASE)
_QTY_PRODUCT_RE = re.compile(
    r"^\s*(\d+)\s*(?:kilo|kg|adet|tane)?\s+(.+?)(?:\s+(?:istiyorum|almak istiyorum|sipari??|siparis).*)?\s*$",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def parse_intent(text: str) -> ParsedIntent:
    raw = text or ""
    t = _norm(raw)
    if not t:
        return ParsedIntent(intent=IntentType.UNKNOWN, raw_text=raw)

    if any(k in t for k in ("yard??m", "yardim", "ne yapabilirsin", "help")):
        return ParsedIntent(intent=IntentType.HELP, raw_text=raw, confidence=0.95)

    if any(k in t for k in ("??r??nleri listele", "urunleri listele", "??r??nleri g??ster", "urunleri goster", "hangi ??r??nler var", "hangi urunler var", "listele")):
        return ParsedIntent(intent=IntentType.LIST_PRODUCTS, raw_text=raw, confidence=0.9)

    if "kargom nerede" in t or "kargo nerede" in t or "takip" in t:
        entities: dict[str, object] = {}
        m = _TRACKING_RE.search(raw)
        if m:
            entities["tracking_number"] = m.group(0).upper()
        return ParsedIntent(intent=IntentType.TRACK_CARGO, entities=entities, raw_text=raw, confidence=0.85)

    if "iptal" in t and ("sipari??" in t or "sipari?" in t or "siparis" in t):
        entities = {}
        order_no_match = _ORDER_NUMBER_RE.search(raw)
        if order_no_match:
            entities["order_number"] = order_no_match.group(0).upper()
        m = _ORDER_ID_RE.search(raw)
        if m:
            entities["order_id"] = int(m.group(1))
        return ParsedIntent(intent=IntentType.CANCEL_ORDER, entities=entities, raw_text=raw, confidence=0.85)

    qty_match = _QTY_PRODUCT_RE.match(raw)
    if qty_match:
        qty = int(qty_match.group(1))
        product_name = qty_match.group(2).strip()
        return ParsedIntent(
            intent=IntentType.CREATE_ORDER,
            entities={"quantity": qty, "product_name": product_name},
            raw_text=raw,
            confidence=0.85,
        )

    if any(k in t for k in ("istiyorum", "sipari??", "sipari?", "siparis", "almak istiyorum")):
        product_guess = re.sub(r"(istiyorum|almak istiyorum|sipari??|sipari?|siparis)", "", t, flags=re.IGNORECASE).strip()
        if product_guess:
            return ParsedIntent(
                intent=IntentType.CREATE_ORDER,
                entities={"quantity": 1, "product_name": product_guess},
                raw_text=raw,
                confidence=0.6,
            )

    return ParsedIntent(intent=IntentType.UNKNOWN, raw_text=raw, confidence=0.0)
