from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Awaitable, Callable
from urllib import error, request

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(dotenv_path=BACKEND_DIR.parent / ".env")

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.order import Order
from services.cargo_service import get_cargo_status, get_estimated_delivery, track_cargo, update_cargo_status
from services.order_access_service import cancel_customer_order, get_customer_order_by_id, get_customer_order_detail
from services.order_service import get_customer_orders
from services.product_service import add_product, check_stock, list_products, low_stock_products, update_stock
from services.support_service import create_support_ticket
from services.user_service_telegram import get_customer_by_telegram_id, get_or_create_customer_from_telegram
from telegram_whatsapp_bot.ai_router import route_text
from telegram_whatsapp_bot.conversation_state import has_active_state
from telegram_whatsapp_bot.order_formatter import resolve_order_id_from_text
from telegram_whatsapp_bot.menus.menu_manager import (
    confirm_ticket_inline_menu,
    customer_cargo_menu,
    customer_main_menu,
    customer_order_menu,
    customer_support_menu,
    seller_cargo_menu,
    seller_main_menu,
    seller_order_menu,
    seller_stock_menu,
    support_feedback_inline_menu,
)

logger = logging.getLogger(__name__)

UNVERIFIED_TELEGRAM_MESSAGE = (
    "Bu Telegram hesabı sistemde kayıtlı bir kullanıcıyla eşleşmiyor."
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
AGENT_API_BASE_URL = os.environ.get("AGENT_API_BASE_URL", "http://127.0.0.1:8000")
AGENT_CHAT_URL = f"{AGENT_API_BASE_URL.rstrip('/')}/agent/chat"

AGENT_HTTP_TIMEOUT_SEC = 25
AGENT_HTTP_RETRIES = 1
MAX_AGENT_HISTORY_MSG = 8

ESCALATION_KEYWORDS = (
    "cozulmedi",
    "ise yaramadi",
    "yetkiliye baglan",
    "destek talebi olustur",
)

CB_SUPPORT_OK = "support_ok"
CB_SUPPORT_NOT_OK = "support_not_ok"
CB_TICKET_CREATE = "ticket_create"
CB_TICKET_CANCEL = "ticket_cancel"


class UserRole(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    SUPERADMIN = "superadmin"


class UserSession:
    __slots__ = (
        "state",
        "last_tracking_number",
        "agent_history",
        "last_support_user_message",
        "last_support_agent_reply",
    )

    def __init__(self) -> None:
        self.state: str | None = None
        self.last_tracking_number: str | None = None
        self.agent_history: list[dict[str, str]] = []
        self.last_support_user_message: str | None = None
        self.last_support_agent_reply: str | None = None


_sessions: dict[int, UserSession] = {}


def get_session(user_id: int) -> UserSession:
    if user_id not in _sessions:
        _sessions[user_id] = UserSession()
    return _sessions[user_id]


def get_user_role(user_id: int) -> UserRole:
    customer = get_customer_by_telegram_id(user_id)
    if customer and getattr(customer, "role", None):
        role_value = getattr(customer.role, "value", customer.role)
        role_value = str(role_value).lower()
        if role_value == "seller":
            return UserRole.SELLER
        if role_value == "cooperative":
            return UserRole.SUPERADMIN
    return UserRole.CUSTOMER


def get_user_role_from_customer(customer: Customer | None) -> UserRole:
    if customer and getattr(customer, "role", None):
        role_value = getattr(customer.role, "value", customer.role)
        role_value = str(role_value).lower()
        if role_value == "seller":
            return UserRole.SELLER
        if role_value == "cooperative":
            return UserRole.SUPERADMIN
    return UserRole.CUSTOMER


def _btn(menu_fn: Callable, row: int, col: int = 0) -> str:
    val = menu_fn().keyboard[row][col]
    return val.text if hasattr(val, "text") else val


BTN_C_ORDER = _btn(customer_main_menu, 0)
BTN_C_CARGO = _btn(customer_main_menu, 1)
BTN_C_SUPPORT = _btn(customer_main_menu, 2)
BTN_C_HELP = _btn(customer_main_menu, 3)

BTN_O_QUERY = _btn(customer_order_menu, 0)
BTN_O_CREATE_AI = _btn(customer_order_menu, 1)
BTN_O_DETAIL = _btn(customer_order_menu, 2)
BTN_BACK = _btn(customer_order_menu, 3)

BTN_CARGO_TRACK = _btn(customer_cargo_menu, 0)
BTN_CARGO_WHERE = _btn(customer_cargo_menu, 1)
BTN_CARGO_ETA = _btn(customer_cargo_menu, 2)

BTN_SUP_ORDER_WHERE = _btn(customer_support_menu, 0)
BTN_SUP_CANCEL_INFO = _btn(customer_support_menu, 1)
BTN_SUP_CARGO_DELAY = _btn(customer_support_menu, 2)
BTN_SUP_PAYMENT = _btn(customer_support_menu, 3)
BTN_SUP_ACCOUNT = _btn(customer_support_menu, 4)
BTN_SUP_WRITE = _btn(customer_support_menu, 5)
BTN_SUP_MORE = _btn(customer_support_menu, 6)

BTN_S_ORDERS = _btn(seller_main_menu, 0)
BTN_S_STOCK = _btn(seller_main_menu, 1)
BTN_S_CARGO = _btn(seller_main_menu, 2)
BTN_S_REPORTS = _btn(seller_main_menu, 3)
BTN_S_HELP = _btn(seller_main_menu, 4)

BTN_STOCK_STATUS = _btn(seller_stock_menu, 0)
BTN_STOCK_LOW = _btn(seller_stock_menu, 1)
BTN_STOCK_ADD = _btn(seller_stock_menu, 2)
BTN_STOCK_UPDATE = _btn(seller_stock_menu, 3)

BTN_SO_TODAY = _btn(seller_order_menu, 0)
BTN_SO_NEW = _btn(seller_order_menu, 1)
BTN_SO_PREPARING = _btn(seller_order_menu, 2)
BTN_SO_DELIVERED = _btn(seller_order_menu, 3)

BTN_SC_TO_SHIP = _btn(seller_cargo_menu, 0)
BTN_SC_STATUS = _btn(seller_cargo_menu, 1)

WEB_SUPPORT_MESSAGE = (
    "🌐 Detaylı işlemler için web panelimizi kullanabilirsiniz.\n"
    "🔗 https://example.com"
)
ORDER_WEB_URL = "https://example.com/order"
ORDER_REDIRECT_MESSAGE = f"Sipariş vermek için sitemizi kullanabilirsiniz: {ORDER_WEB_URL}"

MENU_BUTTON_TEXTS = {
    BTN_C_ORDER, BTN_C_CARGO, BTN_C_SUPPORT, BTN_C_HELP,
    BTN_O_QUERY, BTN_O_CREATE_AI, BTN_O_DETAIL, BTN_BACK,
    BTN_CARGO_TRACK, BTN_CARGO_WHERE, BTN_CARGO_ETA,
    BTN_SUP_ORDER_WHERE, BTN_SUP_CANCEL_INFO, BTN_SUP_CARGO_DELAY, BTN_SUP_PAYMENT, BTN_SUP_ACCOUNT, BTN_SUP_WRITE, BTN_SUP_MORE,
    BTN_S_ORDERS, BTN_S_STOCK, BTN_S_CARGO, BTN_S_REPORTS, BTN_S_HELP,
    BTN_STOCK_STATUS, BTN_STOCK_LOW, BTN_STOCK_ADD, BTN_STOCK_UPDATE,
    BTN_SO_TODAY, BTN_SO_NEW, BTN_SO_PREPARING, BTN_SO_DELIVERED,
    BTN_SC_TO_SHIP, BTN_SC_STATUS,
}

SUPPORT_PRESET_RESPONSES = {
    BTN_SUP_ORDER_WHERE: "Sipariş durumunuzu 'Sipariş Sorgula' menüsünden görebilirsiniz. İsterseniz sipariş numaranızı burada da yazabilirsiniz.",
    BTN_SUP_CANCEL_INFO: "Sipariş iptali için 'Sipariş İptali' menüsüne girip sipariş numaranızı paylaşmanız yeterli.",
    BTN_SUP_CARGO_DELAY: "Gecikme için üzgünüz. Takip numaranızı paylaşırsanız durumu hemen kontrol edelim.",
    BTN_SUP_PAYMENT: "Ödeme ile ilgili sorununuzu güvenle inceleyebiliriz. Gerekirse sizi canlı desteğe yönlendirebiliriz.",
    BTN_SUP_ACCOUNT: "Hesap işlemleri için yardımcı olabilirim. Sorununuzu kısaca yazabilirsiniz.",
}


def _safe_int(value: str) -> int | None:
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return None


def _contains_escalation(text: str) -> bool:
    lowered = (text or "").lower()
    return any(key in lowered for key in ESCALATION_KEYWORDS)


def _add_agent_history(sess: UserSession, role: str, content: str) -> None:
    sess.agent_history.append({"role": role, "content": content})
    if len(sess.agent_history) > MAX_AGENT_HISTORY_MSG:
        sess.agent_history = sess.agent_history[-MAX_AGENT_HISTORY_MSG:]


def _compose_agent_message(sess: UserSession, user_message: str) -> str:
    if not sess.agent_history:
        return user_message
    lines = ["Önceki kısa konuşma özeti:"]
    for m in sess.agent_history:
        who = "Kullanici" if m["role"] == "user" else "Asistan"
        lines.append(f"- {who}: {m['content']}")
    lines.append("")
    lines.append(f"Güncel kullanıcı mesajı: {user_message}")
    return "\n".join(lines)


def _agent_chat_http(message: str, user_id: int) -> tuple[bool, str]:
    sess = get_session(user_id)
    guidance = "Yaniti okunabilir Turkce yaz. Turkce karakterleri dogru kullan."
    payload = {"message": f"{guidance}\n\n{_compose_agent_message(sess, message)}"}
    data = json.dumps(payload).encode("utf-8")

    for _ in range(AGENT_HTTP_RETRIES + 1):
        req = request.Request(
            AGENT_CHAT_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=AGENT_HTTP_TIMEOUT_SEC) as resp:
                body = resp.read().decode("utf-8")
            response_json = json.loads(body)
            reply = (response_json.get("reply") or "").strip()
            if "Ã" in reply or "Å" in reply:
                try:
                    reply = reply.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
                except Exception:
                    pass
            if reply:
                _add_agent_history(sess, "user", message)
                _add_agent_history(sess, "assistant", reply)
                return True, reply
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            logger.exception("agent.http_error status=%s detail=%s", exc.code, detail[:500])
        except Exception:
            logger.exception("agent.request_failed")

    return False, "Su anda yanit veremiyorum. Lutfen biraz sonra tekrar deneyin."


def _create_ticket_from_session(customer_id: int, telegram_user_id: int, sess: UserSession) -> tuple[bool, str]:
    user_msg = sess.last_support_user_message or "Destek talebi"
    agent_msg = sess.last_support_agent_reply or "Agent yaniti yok"
    ticket_message = (
        "Telegram destek escalation\n"
        f"Kullanici mesaji: {user_msg}\n"
        f"Agent son yanit: {agent_msg[:800]}"
    )
    result = create_support_ticket(
        customer_id=customer_id,
        telegram_user_id=telegram_user_id,
        subject="telegram-support",
        message=ticket_message,
    )
    if result.get("success"):
        return True, "Destek talebiniz alindi. En kisa surede geri donus yapilacaktir."
    return False, result.get("message", "Destek talebi olusturulamadi.")


def fmt_order_basic(o: dict) -> str:
    order_no = o.get("order_number") or f"ORD-{int(o['id']):06d}"
    created_at = o.get("created_at") or "-"
    status_map = {
        "pending": "Hazırlanıyor",
        "preparing": "Hazırlanıyor",
        "shipped": "Kargoda",
        "delivered": "Teslim Edildi",
        "cancelled": "İptal Edildi",
    }
    status_text = status_map.get(str(o.get("status", "")).lower(), o.get("status") or "-")
    return (
        "<b>📦 Sipariş Bilgileri</b>\n\n"
        f"🆔 Sipariş No:\n<code>{order_no}</code>\n\n"
        f"📅 Tarih:\n{created_at}\n\n"
        f"📦 Durum:\n{status_text}\n\n"
        f"💰 Toplam:\n{o.get('total_amount')} TL\n\n"
        "🌐 Detaylı işlemler:\n"
        "https://example.com"
    )


def fmt_order_detail(o: dict) -> str:
    order_no = o.get("order_number") or f"ORD-{int(o['id']):06d}"
    status_map = {
        "pending": "Hazırlanıyor",
        "preparing": "Hazırlanıyor",
        "shipped": "Kargoda",
        "delivered": "Teslim Edildi",
        "cancelled": "İptal Edildi",
    }
    status_text = status_map.get(str(o.get("status", "")).lower(), o.get("status") or "-")
    lines = [
        "<b>📦 Sipariş Bilgileri</b>",
        "",
        "🆔 Sipariş No:",
        f"<code>{order_no}</code>",
        "",
        "📦 Durum:",
        status_text,
        "",
        "🛒 Ürünler:",
    ]
    for item in o.get("items", []):
        lines.append(
            f"- {item.get('product_name', 'Ürün')} | {item['quantity']} adet"
        )
    lines.extend([
        "",
        "🚚 Kargo:",
        status_text,
        "",
        "💰 Toplam:",
        f"{o.get('total_amount')} TL",
        "",
        "🌐 Detaylı işlemler:",
        "https://example.com",
    ])
    return "\n".join(lines)


def fmt_cargo(c: dict) -> str:
    return (
        "<b>🚚 Kargo Bilgisi</b>\n\n"
        f"🆔 Sipariş: <code>ORD-{int(c['order_id']):06d}</code>\n"
        f"🔢 Takip No: <code>{c['tracking_number']}</code>\n"
        f"📦 Sipariş Durumu: {c['order_status']}\n"
        f"🚚 Kargo Durumu: {c['cargo_status']}"
    )


async def _reply(update: Update, text: str, markup=None) -> None:
    try:
        await update.message.reply_text(
            text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception:
        await update.message.reply_text(text, reply_markup=markup, disable_web_page_preview=True)


async def _error(update: Update, message: str, markup=None) -> None:
    await _reply(update, f"❌ {message}", markup)


def _list_orders_by_status_local(status: str, limit: int = 20) -> dict:
    db = SessionLocal()
    try:
        rows = (
            db.query(Order, Customer)
            .join(Customer, Customer.id == Order.customer_id)
            .filter(Order.status == status)
            .order_by(Order.id.desc())
            .limit(limit)
            .all()
        )
        data = [
            {
                "id": o.id,
                "customer_name": c.full_name if c else None,
                "status": o.status,
                "total_amount": float(o.total_amount or 0),
            }
            for o, c in rows
        ]
        return {"success": True, "data": data}
    finally:
        db.close()


def _seller_report_summary_local() -> dict:
    db = SessionLocal()
    try:
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == "pending").count()
        preparing_orders = db.query(Order).filter(Order.status == "preparing").count()
        shipped_orders = db.query(Order).filter(Order.status == "shipped").count()
        delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
        cancelled_orders = db.query(Order).filter(Order.status == "cancelled").count()
        gross_revenue = sum(float(x[0] or 0) for x in db.query(Order.total_amount).all())
        return {
            "success": True,
            "data": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "preparing_orders": preparing_orders,
                "shipped_orders": shipped_orders,
                "delivered_orders": delivered_orders,
                "cancelled_orders": cancelled_orders,
                "gross_revenue": gross_revenue,
            },
        }
    finally:
        db.close()


async def _state_order_query_id(update: Update, sess: UserSession) -> None:
    order_id = resolve_order_id_from_text(update.message.text)
    if order_id is None:
        await _error(update, "Gecerli bir siparis referansi girin. Ornek: 1 veya ORD-000001", customer_order_menu())
        return
    sess.state = None
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    result = get_customer_order_by_id(customer.id, order_id)
    if result.get("success"):
        await _reply(update, fmt_order_basic(result["data"]), customer_order_menu())
    else:
        await _error(update, result.get("message", "Siparis bulunamadi."), customer_order_menu())


async def _state_order_detail_id(update: Update, sess: UserSession) -> None:
    order_id = resolve_order_id_from_text(update.message.text)
    if order_id is None:
        await _error(update, "Gecerli bir siparis referansi girin. Ornek: 1 veya ORD-000001", customer_order_menu())
        return
    sess.state = None
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    result = get_customer_order_detail(customer.id, order_id)
    if result.get("success"):
        await _reply(update, fmt_order_detail(result["data"]), customer_order_menu())
    else:
        await _error(update, result.get("message", "Siparis detayi bulunamadi."), customer_order_menu())


def _fmt_customer_orders_list(orders: list[dict]) -> str:
    if not orders:
        return "Henüz siparişiniz bulunmuyor."
    blocks = [fmt_order_basic(o) for o in orders[:10]]
    return "\n\n".join(blocks)


async def _state_cancel_order_id(update: Update, sess: UserSession) -> None:
    order_id = resolve_order_id_from_text(update.message.text)
    if order_id is None:
        await _error(update, "Gecerli bir siparis referansi girin. Ornek: 1 veya ORD-000001", customer_order_menu())
        return
    sess.state = None
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    result = cancel_customer_order(customer.id, order_id)
    if result.get("success"):
        await _reply(update, f"✅ {result.get('message')}\n\n{fmt_order_basic(result['data'])}", customer_order_menu())
    else:
        await _error(update, result.get("message", "Siparis iptal edilemedi."), customer_order_menu())


async def _state_order_create_ai(update: Update, sess: UserSession) -> None:
    text = (update.message.text or "").strip()
    if not text:
        await _error(update, "Lütfen sipariş isteğinizi yazın.", customer_order_menu())
        return
    sess.state = None
    # AGENT-LINKED MENU: natural language order creation.
    ok, reply = _agent_chat_http(text, update.message.from_user.id)
    if ok:
        await _reply(update, reply, customer_order_menu())
    else:
        await _error(update, "Sipariş asistanı şu an yanıt veremiyor.", customer_order_menu())


async def _state_tracking(update: Update, sess: UserSession, *, with_eta: bool = False) -> None:
    tracking_number = update.message.text.strip().upper()
    sess.state = None
    sess.last_tracking_number = tracking_number

    if with_eta:
        result = get_estimated_delivery(tracking_number)
        if result.get("success"):
            data = result["data"]
            await _reply(
                update,
                f"{fmt_cargo(data)}\n Tahmini Teslim: {data['estimated_delivery_date']}",
                customer_cargo_menu(),
            )
        else:
            await _error(update, result.get("message", "Tahmini teslim alinamadi."), customer_cargo_menu())
    else:
        result = track_cargo(tracking_number)
        if result.get("success"):
            await _reply(update, fmt_cargo(result["data"]), customer_cargo_menu())
        else:
            await _error(update, result.get("message", "Kargo bilgisi alinamadi."), customer_cargo_menu())


async def _state_support_agent(update: Update, sess: UserSession) -> None:
    text = (update.message.text or "").strip()
    if not text:
        await _error(update, "Lutfen sorununuzu yazin.", customer_support_menu())
        return

    customer = get_or_create_customer_from_telegram(update.message.from_user)
    sess.last_support_user_message = text

    if _contains_escalation(text):
        ok, msg = _create_ticket_from_session(customer.id, update.message.from_user.id, sess)
        sess.state = None
        if ok:
            await _reply(update, msg, customer_support_menu())
        else:
            await _error(update, msg, customer_support_menu())
        return

    ok, reply = _agent_chat_http(f"Destek talebi: {text}", update.message.from_user.id)
    sess.last_support_agent_reply = reply
    sess.state = None
    if ok:
        await _reply(update, reply, customer_support_menu())
        await _reply(update, "Bu yanit sorununuzu cozdu mu?", support_feedback_inline_menu())
        return

    ok_ticket, ticket_msg = _create_ticket_from_session(customer.id, update.message.from_user.id, sess)
    if ok_ticket:
        await _reply(update, f"Su anda yanit veremiyorum. {ticket_msg}", customer_support_menu())
    else:
        await _error(update, f"Su anda yanit veremiyorum. {ticket_msg}", customer_support_menu())


async def _state_stock_product_id(update: Update, sess: UserSession) -> None:
    product_id = _safe_int(update.message.text)
    if product_id is None:
        await _error(update, "Gecerli bir urun ID girin. Ornek: 1", seller_stock_menu())
        return
    sess.state = None
    result = check_stock(product_id)
    if result.get("success"):
        data = result["data"]
        await _reply(
            update,
            f" {data['product_name']}\n"
            f"Stok: {data['stock_quantity']}\n"
            f"Dk stok: {' Evet' if data['is_low_stock'] else ' Hayr'}",
            seller_stock_menu(),
        )
    else:
        await _error(update, result.get("message", "Stok bilgisi alinamadi."), seller_stock_menu())


async def _state_stock_add(update: Update, sess: UserSession) -> None:
    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 3:
        await _error(update, "Format: ürün adı, fiyat, başlangıç stok\nÖrnek: Zeytin, 120, 50", seller_stock_menu())
        return

    name = parts[0]
    try:
        price = float(parts[1])
        stock = int(parts[2])
    except ValueError:
        await _error(update, "Fiyat say, stok tam say olmal.", seller_stock_menu())
        return

    sess.state = None
    result = add_product(name=name, price=price, stock_quantity=stock)
    if result.get("success"):
        data = result["data"]
        await _reply(
            update,
            f"Urun eklendi: #{data['id']} {data['name']} | Fiyat: {data['price']} | Stok: {data['stock_quantity']}",
            seller_stock_menu(),
        )
    else:
        await _error(update, result.get("message", "Urun eklenemedi."), seller_stock_menu())


async def _state_stock_update(update: Update, sess: UserSession) -> None:
    raw = update.message.text.strip()
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        await _error(update, "Format: urun_id veya urun_adi, degisim\nOrnek: 3, -5 veya Organik Bal, 20", seller_stock_menu())
        return

    product_ref = parts[0]
    try:
        delta = int(parts[1])
    except ValueError:
        await _error(update, "Degisim tam sayi olmali. Ornek: -5 veya 20", seller_stock_menu())
        return

    product_id: int | None = None
    try:
        product_id = int(product_ref)
    except ValueError:
        products_resp = list_products()
        products = products_resp.get("data", []) if products_resp.get("success") else []
        ref_lower = product_ref.lower()
        match = next((p for p in products if str(p.get("name", "")).lower() == ref_lower), None)
        if match:
            product_id = int(match["id"])
        else:
            await _error(update, f"Urun bulunamadi: {product_ref}", seller_stock_menu())
            return

    sess.state = None
    result = update_stock(product_id, delta, note="Seller panel stock update")
    if result.get("success"):
        data = result["data"]
        await _reply(
            update,
            f"Stok guncellendi\nUrun: {data['product_name']}\nOnce: {data['previous_stock']}\nSonra: {data['new_stock']}",
            seller_stock_menu(),
        )
    else:
        await _error(update, result.get("message", "Stok guncellenemedi."), seller_stock_menu())


async def _state_seller_cargo_status_order_id(update: Update, sess: UserSession) -> None:
    order_id = _safe_int(update.message.text)
    if order_id is None:
        await _error(update, "Gecerli bir siparis referansi girin. Ornek: 1 veya ORD-000001", seller_cargo_menu())
        return
    sess.state = None
    result = get_cargo_status(order_id)
    if result.get("success"):
        await _reply(update, fmt_cargo(result["data"]), seller_cargo_menu())
    else:
        await _error(update, result.get("message", "Kargo durumu alinamadi."), seller_cargo_menu())




_STATE_HANDLERS: dict[str, Callable[[Update, UserSession], Awaitable[None]]] = {
    "waiting_order_query_id": _state_order_query_id,
    "waiting_order_detail_id": _state_order_detail_id,
    "waiting_cancel_order_id": _state_cancel_order_id,
    "waiting_order_create_ai": _state_order_create_ai,
    "waiting_tracking_number": lambda u, s: _state_tracking(u, s),
    "waiting_tracking_where": lambda u, s: _state_tracking(u, s),
    "waiting_tracking_eta": lambda u, s: _state_tracking(u, s, with_eta=True),
    "waiting_support_agent": _state_support_agent,
    "waiting_stock_product_id": _state_stock_product_id,
    "waiting_stock_add": _state_stock_add,
    "waiting_stock_update": _state_stock_update,
    "waiting_seller_cargo_status_order_id": _state_seller_cargo_status_order_id,
}


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    sess = get_session(user_id)
    customer = get_or_create_customer_from_telegram(query.from_user)

    if query.data == CB_SUPPORT_OK:
        await query.edit_message_text("Geri bildiriminiz alindi.")
        return
    if query.data == CB_SUPPORT_NOT_OK:
        await query.edit_message_text("Isterseniz destek talebi olusturabilirim.", reply_markup=confirm_ticket_inline_menu())
        return
    if query.data == CB_TICKET_CREATE:
        ok, msg = _create_ticket_from_session(customer.id, user_id, sess)
        await query.edit_message_text(msg)
        return
    if query.data == CB_TICKET_CANCEL:
        await query.edit_message_text("Destek menusune donebilirsiniz.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    text = update.message.text
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    if not customer:
        await _reply(update, UNVERIFIED_TELEGRAM_MESSAGE)
        return
    role = get_user_role_from_customer(customer)
    sess = get_session(user_id)

    if text == BTN_BACK:
        sess.state = None
        if role in (UserRole.SELLER, UserRole.SUPERADMIN):
            await _reply(update, "⬅️ Ana Menü", seller_main_menu())
        else:
            await _reply(update, "⬅️ Ana Menü", customer_main_menu())
        return

    if sess.state in _STATE_HANDLERS:
        await _STATE_HANDLERS[sess.state](update, sess)
        return

    # Priority 1: active conversational AI state consumes message first.
    ai_checked = False
    if has_active_state(user_id):
        ai_result = route_text(user_id=user_id, customer=customer, text=text)
        ai_checked = True
        if ai_result.handled:
            await _reply(update, ai_result.response_text)
            return

    # Priority 2: Natural-language orchestration, then menu fallback.
    if text not in MENU_BUTTON_TEXTS and not ai_checked:
        ai_result = route_text(user_id=user_id, customer=customer, text=text)
        if ai_result.handled:
            await _reply(update, ai_result.response_text)
            return

    if role == UserRole.CUSTOMER and _contains_escalation(text) and sess.last_support_user_message:
        ok, msg = _create_ticket_from_session(customer.id, user_id, sess)
        if ok:
            await _reply(update, msg, customer_support_menu())
        else:
            await _error(update, msg, customer_support_menu())
        return

    if role == UserRole.CUSTOMER:
        await _customer_menu_router(update, text, sess)
    else:
        await _seller_menu_router(update, text, sess)


async def _customer_menu_router(update: Update, text: str, sess: UserSession) -> None:
    if text == BTN_C_ORDER:
        await _reply(
            update,
            "📦 <b>Sipariş İşlemleri</b>\n\nLütfen yapmak istediğiniz işlemi seçin:",
            customer_order_menu(),
        )
    elif text == BTN_C_CARGO:
        await _reply(update, "🚚 <b>Kargo İşlemleri</b>\n\nLütfen yapmak istediğiniz işlemi seçin:", customer_cargo_menu())
    elif text == BTN_C_SUPPORT:
        await _reply(update, "📞 <b>Destek</b>\n\nLütfen konunuzu seçin:", customer_support_menu())
    elif text == BTN_C_HELP:
        await _reply(
            update,
            "<b>Yardim Menusu</b>\n\n"
            "- Siparis islemleri: Siparis sorgula ve siparislerimden takibini yapin.\n"
            "- Kargo islemleri: Takip numarasi ile anlik durum gorun.\n"
            "- Destek: Ozel durumlar icin web destek paneline gecin.\n\n"
            "Web: https://example.com/support",
            customer_main_menu(),
        )
    elif text == BTN_SUP_CANCEL_INFO:
        await _reply(update, "Iptal islemleri icin web sitemizi kullanabilirsiniz:\nhttps://example.com/support", customer_support_menu())
    elif text == BTN_SUP_CARGO_DELAY:
        sess.state = "waiting_tracking_number"
        await _reply(update, "Kargo gecikmesi icin takip/siparis numaranizi yazin. Ornek: ORD-000001", customer_cargo_menu())
    elif text == BTN_SUP_PAYMENT:
        await _reply(update, "Odeme islemleri icin web sitemizi kullanabilirsiniz:\nhttps://example.com/support", customer_support_menu())
    elif text == BTN_SUP_ACCOUNT:
        await _reply(update, "Hesap islemleri icin web sitemizi kullanabilirsiniz:\nhttps://example.com/support", customer_support_menu())
    elif text in SUPPORT_PRESET_RESPONSES:
        await _reply(update, SUPPORT_PRESET_RESPONSES[text], customer_support_menu())
    elif text == BTN_SUP_WRITE:
        sess.state = "waiting_support_agent"
        await _reply(update, "Sorununuzu yazın, hemen yardımcı olayım.", customer_support_menu())
    elif text == BTN_SUP_MORE:
        await _reply(update, WEB_SUPPORT_MESSAGE, customer_support_menu())
    elif text == BTN_O_QUERY:
        sess.state = "waiting_order_query_id"
        await _reply(update, "Lütfen sipariş numaranızı yazın. Örnek: 1 veya ORD-000001", customer_order_menu())
    elif text == BTN_O_CREATE_AI:
        await _reply(update, ORDER_REDIRECT_MESSAGE, customer_order_menu())
    elif text == BTN_O_DETAIL:
        customer = get_or_create_customer_from_telegram(update.message.from_user)
        result = get_customer_orders(customer.id)
        if result.get("success"):
            await _reply(update, _fmt_customer_orders_list(result.get("data", [])), customer_order_menu())
        else:
            await _error(update, result.get("message", "Siparisleriniz alinamadi."), customer_order_menu())
    elif text == BTN_CARGO_TRACK:
        sess.state = "waiting_tracking_number"
        await _reply(update, "Lutfen takip numaranizi yazin. Ornek: ORD-000001", customer_cargo_menu())
    elif text == BTN_CARGO_WHERE:
        if sess.last_tracking_number:
            result = track_cargo(sess.last_tracking_number)
            if result.get("success"):
                await _reply(update, fmt_cargo(result["data"]), customer_cargo_menu())
            else:
                await _error(update, result.get("message", "Kargo bilgisi alinamadi."), customer_cargo_menu())
        else:
            sess.state = "waiting_tracking_where"
            await _reply(update, "Önce takip numaranızı yazın. Örnek: ORD-000001", customer_cargo_menu())
    elif text == BTN_CARGO_ETA:
        if sess.last_tracking_number:
            result = get_estimated_delivery(sess.last_tracking_number)
            if result.get("success"):
                data = result["data"]
                await _reply(
                    update,
                    f"{fmt_cargo(data)}\nTahmini teslim: {data['estimated_delivery_date']}",
                    customer_cargo_menu(),
                )
            else:
                await _error(update, result.get("message", "Tahmini teslim alinamadi."), customer_cargo_menu())
        else:
            sess.state = "waiting_tracking_eta"
            await _reply(update, "Tahmini teslim için takip numaranızı yazın. Örnek: ORD-000001", customer_cargo_menu())
    else:
        await _reply(
            update,
            "Mesajınızı anlayamadım. Lütfen menüden bir seçenek seçin.",
            customer_main_menu(),
        )


async def _seller_menu_router(update: Update, text: str, sess: UserSession) -> None:
    if text == BTN_S_ORDERS:
        await _reply(update, "Siparis yonetimi menusundesiniz.", seller_order_menu())
    elif text == BTN_S_STOCK:
        await _reply(update, "Stok yonetimi menusundesiniz.", seller_stock_menu())
    elif text == BTN_S_CARGO:
        await _reply(update, "Kargo yonetimi menusundesiniz.", seller_cargo_menu())
    elif text == BTN_S_REPORTS:
        result = _seller_report_summary_local()
        d = result["data"]
        await _reply(
            update,
            "<b>📊 Rapor Özeti</b>\n\n"
            f"• Toplam Sipariş: {d['total_orders']}\n"
            f"• Yeni (Pending): {d['pending_orders']}\n"
            f"• Hazırlanan: {d['preparing_orders']}\n"
            f"• Kargoda: {d['shipped_orders']}\n"
            f"• Teslim Edilen: {d['delivered_orders']}\n"
            f"• İptal Edilen: {d['cancelled_orders']}\n"
            f"• Ciro: {d['gross_revenue']} TL\n\n"
            "Detaylı bilgi için: www.example.com",
            seller_main_menu(),
        )
    elif text == BTN_S_HELP:
        await _reply(
            update,
            "<b>ℹ️ Satıcı Yardım</b>\n\n"
            "• Sipariş Yönetimi: Günlük/yeni/hazırlanan/teslim siparişleri takip edin.\n"
            "• Stok Yönetimi: Ürün ekleyin, stok durumunu kontrol edin, stok değişimini güncelleyin.\n"
            "• Kargo Yönetimi: Kargoya verilecek siparişleri ve kargo durumlarını görüntüleyin.\n\n"
            "Detaylı bilgi için: www.example.com",
            seller_main_menu(),
        )
    elif text == BTN_STOCK_STATUS:
        sess.state = "waiting_stock_product_id"
        await _reply(update, "Urun ID girin. Ornek: 1", seller_stock_menu())
    elif text == BTN_STOCK_LOW:
        result = low_stock_products()
        rows = result.get("data", [])
        if not rows:
            await _reply(update, "Azalan stokta urun bulunmuyor.", seller_stock_menu())
        else:
            lines = [" Azalan Stoklar:"]
            for p in rows:
                lines.append(f"   #{p['id']} {p['name']}  {p['stock_quantity']} adet")
            await _reply(update, "\n".join(lines), seller_stock_menu())
    elif text == BTN_STOCK_ADD:
        sess.state = "waiting_stock_add"
        await _reply(update, "Urun ekleme formati: urun adi, fiyat, stok", seller_stock_menu())
    elif text == BTN_STOCK_UPDATE:
        sess.state = "waiting_stock_update"
        products_result = list_products()
        rows = products_result.get("data", []) if products_result.get("success") else []
        if rows:
            lines = ["Urunler:"]
            for p in rows[:30]:
                lines.append(f"#{p['id']} {p['name']} | Stok: {p['stock_quantity']}")
            lines.append("")
            lines.append("Stok guncelleme formati: urun_id veya urun_adi, degisim")
            lines.append("Ornek: 3, -5 veya Organik Bal, 20")
            await _reply(update, "\n".join(lines), seller_stock_menu())
        else:
            await _reply(update, "Stok guncelleme formati: urun_id veya urun_adi, degisim", seller_stock_menu())
    elif text == BTN_SO_NEW:
        result = _list_orders_by_status_local("pending", limit=20)
        rows = result.get("data", [])
        await _reply(update, "\n\n".join(fmt_order_basic(o) for o in rows[:10]) if rows else "Yeni siparis yok.", seller_order_menu())
    elif text == BTN_SO_PREPARING:
        result = _list_orders_by_status_local("preparing", limit=20)
        rows = result.get("data", [])
        await _reply(update, "\n\n".join(fmt_order_basic(o) for o in rows[:10]) if rows else "Hazirlanan siparis yok.", seller_order_menu())
    elif text == BTN_SO_DELIVERED:
        result = _list_orders_by_status_local("delivered", limit=20)
        rows = result.get("data", [])
        await _reply(update, "\n\n".join(fmt_order_basic(o) for o in rows[:10]) if rows else "Teslim edilen siparis yok.", seller_order_menu())
    elif text == BTN_SO_TODAY:
        db = SessionLocal()
        try:
            rows = (
                db.query(Order, Customer)
                .join(Customer, Customer.id == Order.customer_id)
                .filter(Order.created_at >= date.today())
                .order_by(Order.id.desc())
                .limit(10)
                .all()
            )
            data = [{"id": o.id, "customer_name": c.full_name if c else None, "status": o.status, "total_amount": float(o.total_amount or 0)} for o, c in rows]
        finally:
            db.close()
        await _reply(update, "\n\n".join(fmt_order_basic(o) for o in data) if data else "Bugun siparis yok.", seller_order_menu())
    elif text == BTN_SC_TO_SHIP:
        result = _list_orders_by_status_local("preparing", limit=20)
        rows = result.get("data", [])
        if rows:
            lines = [" Kargoya verilecek sipariler:"]
            for o in rows[:15]:
                lines.append(f"   #{o['id']} {o.get('customer_name') or 'Müşteri'} | {o.get('total_amount')} TL")
            await _reply(update, "\n".join(lines), seller_cargo_menu())
        else:
            await _reply(update, "Kargoya verilecek siparis yok.", seller_cargo_menu())
    elif text == BTN_SC_STATUS:
        sess.state = "waiting_seller_cargo_status_order_id"
        await _reply(update, "Siparis ID girin. Ornek: 1", seller_cargo_menu())
    else:
        await _reply(
            update,
            "Mesajinizi anlayamadim. Lutfen menuden bir secenek secin.",
            seller_main_menu(),
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    sess = get_session(user_id)
    sess.state = None
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    if not customer:
        await _reply(update, UNVERIFIED_TELEGRAM_MESSAGE)
        return
    role = get_user_role_from_customer(customer)
    if role in (UserRole.SELLER, UserRole.SUPERADMIN):
        await _reply(
            update,
            "🌿 <b>Nexus Kooperatif Yönetim Sistemine Hoş Geldiniz!</b>\n\nAşağıdaki menüden yapmak istediğiniz işlemi seçebilirsiniz.",
            seller_main_menu(),
        )
    else:
        await _reply(
            update,
            "🌿 <b>Nexus Kooperatif Yönetim Sistemine Hoş Geldiniz!</b>\n\nAşağıdaki menüden yapmak istediğiniz işlemi seçebilirsiniz.",
            customer_main_menu(),
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    sess = get_session(user_id)
    customer = get_or_create_customer_from_telegram(query.from_user)
    if not customer:
        await query.edit_message_text(UNVERIFIED_TELEGRAM_MESSAGE)
        return

    if query.data == CB_SUPPORT_OK:
        await query.edit_message_text("Geri bildiriminiz alindi.")
    elif query.data == CB_SUPPORT_NOT_OK:
        await query.edit_message_text("Destek talebi olusturmak ister misiniz?", reply_markup=confirm_ticket_inline_menu())
    elif query.data == CB_TICKET_CREATE:
        ok, msg = _create_ticket_from_session(customer.id, user_id, sess)
        await query.edit_message_text(f"{'' if ok else ''} {msg}")
    elif query.data == CB_TICKET_CANCEL:
        await query.edit_message_text("Tamam, destek menusunden devam edebilirsiniz.")


def run_telegram_bot() -> None:
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadi. Proje kokundeki .env dosyasini kontrol edin.")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("menu", cmd_start))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
