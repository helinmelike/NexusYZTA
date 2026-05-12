from __future__ import annotations

import re

from services.cargo_service import track_cargo
from services.order_access_service import cancel_customer_order
from services.order_service import create_order, get_order_by_id
from services.product_service import list_products
from telegram_whatsapp_bot.conversation_state import clear_state, get_state, get_user_session, set_state
from telegram_whatsapp_bot.intent_parser import parse_intent
from telegram_whatsapp_bot.intent_types import IntentType, RouteResult
from telegram_whatsapp_bot.order_formatter import format_order_success, resolve_order_id_from_text


def _extract_tracking(text: str) -> str | None:
    m = re.search(r"\bORD-\d{6,}\b", text or "", re.IGNORECASE)
    return m.group(0).upper() if m else None


def _extract_order_id(text: str) -> int | None:
    return resolve_order_id_from_text(text)


def _is_negative(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ("hayır", "hayir", "yok", "bilmiyorum", "iptal"))


def _is_confirm(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in ("onay", "evet", "tamam", "olur", "onaylıyorum", "onayliyorum"))


def _format_products() -> tuple[list[dict], str]:
    result = list_products()
    rows = result.get("data", []) if result.get("success") else []
    if not rows:
        return [], "Şu an listelenecek ürün bulunamadı."
    lines = ["Ürünler:"]
    for p in rows[:30]:
        lines.append(f"- #{p['id']} {p['name']} | {p['price']} TL | stok: {p['stock_quantity']}")
    return rows, "\n".join(lines)


def _find_product_candidates(product_name: str) -> list[dict]:
    rows, _ = _format_products()
    q = (product_name or "").strip().lower()
    if not q:
        return []
    exact = [p for p in rows if p["name"].strip().lower() == q]
    if exact:
        return exact
    return [p for p in rows if q in p["name"].strip().lower()]


def route_text(user_id: int, customer, text: str) -> RouteResult:
    state = get_state(user_id)
    session = get_user_session(user_id)

    if state == "awaiting_order_confirmation":
        pending = session.get("pending_order") or {}
        product_name = str(pending.get("product_name", ""))
        quantity = int(pending.get("quantity", 1))
        if _is_confirm(text):
            ok_count = 0
            fail_message = ""
            last_success_data: dict | None = None
            for _ in range(max(1, quantity)):
                resp = create_order(customer.full_name, product_name)
                if resp.get("success"):
                    ok_count += 1
                    last_success_data = resp.get("data") or {}
                else:
                    fail_message = resp.get("message", "Sipariş oluşturulamadı.")
                    break
            clear_state(user_id)
            if ok_count == quantity:
                order_data = last_success_data or {}
                order_id = order_data.get("order_id")
                if order_id and not order_data.get("order_number"):
                    detail = get_order_by_id(int(order_id))
                    if detail.get("success") and detail.get("data"):
                        order_data = {
                            "order_id": detail["data"].get("id"),
                            "order_number": detail["data"].get("order_number"),
                        }
                return RouteResult(True, format_order_success(order_data, product_name, quantity))
            if ok_count > 0:
                return RouteResult(True, f"Kısmi başarı: {ok_count}/{quantity} sipariş oluşturuldu. Son hata: {fail_message}")
            return RouteResult(True, f"Sipariş oluşturulamadı: {fail_message}")
        if _is_negative(text):
            clear_state(user_id)
            return RouteResult(True, "Tamam, sipariş işlemini iptal ettim.")
        return RouteResult(True, "Siparişi onaylıyor musunuz? (evet/hayır)")

    if state == "awaiting_product_selection":
        candidates = session.get("product_candidates") or []
        quantity = int(session.get("pending_quantity", 1))
        selected = None
        if text.strip().isdigit():
            selected_id = int(text.strip())
            for p in candidates:
                if int(p["id"]) == selected_id:
                    selected = p
                    break
        if not selected:
            return RouteResult(True, "Lütfen listeden bir ürün ID'si yazın.")
        set_state(user_id, "awaiting_order_confirmation", pending_order={"product_name": selected["name"], "quantity": quantity})
        return RouteResult(True, f"{quantity} adet '{selected['name']}' için sipariş oluşturmamı onaylıyor musunuz? (evet/hayır)")

    if state == "awaiting_cargo_id":
        tracking = _extract_tracking(text)
        if tracking:
            clear_state(user_id)
            tr = track_cargo(tracking)
            if tr.get("success"):
                d = tr["data"]
                return RouteResult(True, f"Kargo durumu:\nTakip: {d['tracking_number']}\nSipariş: {d['order_status']}\nKargo: {d['cargo_status']}")
            return RouteResult(True, tr.get("message", "Kargo bilgisi alınamadı."))
        return RouteResult(True, "Takip numarasını ORD-000001 formatında paylaşır mısınız?")

    if state == "awaiting_cancel_order_id":
        order_id = _extract_order_id(text)
        if order_id is not None:
            clear_state(user_id)
            result = cancel_customer_order(customer.id, order_id)
            if result.get("success"):
                d = result["data"]
                return RouteResult(True, f"Sipariş iptal edildi.\n#{d['id']} | durum: {d['status']} | toplam: {d['total_amount']} TL")
            return RouteResult(True, result.get("message", "Sipariş iptal edilemedi."))
        return RouteResult(True, "Lütfen sipariş numarası yazın. Örnek: 12 veya ORD-000012")

    parsed = parse_intent(text)

    if parsed.intent == IntentType.LIST_PRODUCTS:
        _, product_text = _format_products()
        return RouteResult(True, product_text)

    if parsed.intent == IntentType.HELP:
        return RouteResult(True, "Şunları yapabilirim:\n- 'ürünleri listele'\n- '2 kilo tarhana istiyorum'\n- 'kargom nerede ORD-000001'\n- 'sipariş 12 iptal et'\nAyrıca menüden de işlem yapabilirsiniz.")

    if parsed.intent == IntentType.TRACK_CARGO:
        tracking = parsed.entities.get("tracking_number")
        if not tracking:
            set_state(user_id, "awaiting_cargo_id")
            return RouteResult(True, "Takip numarasını paylaşır mısınız? Örnek: ORD-000001")
        tr = track_cargo(str(tracking))
        if tr.get("success"):
            d = tr["data"]
            return RouteResult(True, f"Kargo durumu:\nTakip: {d['tracking_number']}\nSipariş: {d['order_status']}\nKargo: {d['cargo_status']}")
        return RouteResult(True, tr.get("message", "Kargo bilgisi alınamadı."))

    if parsed.intent == IntentType.CANCEL_ORDER:
        order_id = parsed.entities.get("order_id")
        if order_id is None:
            order_ref = parsed.entities.get("order_number")
            if isinstance(order_ref, str):
                order_id = resolve_order_id_from_text(order_ref)
        if order_id is None:
            set_state(user_id, "awaiting_cancel_order_id")
            return RouteResult(True, "İptal için sipariş numarasını yazar mısınız? Örnek: 12 veya ORD-000012")
        result = cancel_customer_order(customer.id, int(order_id))
        if result.get("success"):
            d = result["data"]
            return RouteResult(True, f"Sipariş iptal edildi.\n#{d['id']} | durum: {d['status']} | toplam: {d['total_amount']} TL")
        return RouteResult(True, result.get("message", "Sipariş iptal edilemedi."))

    if parsed.intent == IntentType.CREATE_ORDER:
        quantity = int(parsed.entities.get("quantity", 1))
        product_name = str(parsed.entities.get("product_name", "")).strip()
        if not product_name:
            return RouteResult(True, "Ürün adını da yazabilir misiniz? Örnek: 2 kilo tarhana")

        matches = _find_product_candidates(product_name)
        if not matches:
            rows, _ = _format_products()
            suggestions = [p["name"] for p in rows if product_name.split()[0].lower() in p["name"].lower()][:5]
            if suggestions:
                return RouteResult(True, "Bu isimle ürün bulamadım. Yakın ürünler:\n- " + "\n- ".join(suggestions))
            return RouteResult(True, "Bu isimle ürün bulamadım. 'ürünleri listele' yazarak ürünleri görebilirsiniz.")

        if len(matches) > 1:
            lines = ["Birden fazla ürün eşleşti, hangisini istediğinizi netleştirir misiniz?"]
            for p in matches[:10]:
                lines.append(f"- #{p['id']} {p['name']} (stok {p['stock_quantity']})")
            set_state(user_id, "awaiting_product_selection", product_candidates=matches, pending_quantity=quantity)
            return RouteResult(True, "\n".join(lines))

        target = matches[0]
        set_state(user_id, "awaiting_order_confirmation", pending_order={"product_name": target["name"], "quantity": quantity})
        return RouteResult(True, f"{quantity} adet '{target['name']}' için sipariş oluşturmamı onaylıyor musunuz? (evet/hayır)")

    return RouteResult(False, "")
