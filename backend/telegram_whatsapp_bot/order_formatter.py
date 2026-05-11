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


def format_warehouse_report(orders_data: list[dict[str, Any]]) -> str:
    if not orders_data:
        return "📦 <b>Bugün hazırlanacak yeni sipariş bulunmuyor.</b>"
    
    report = "📋 <b>GÜNLÜK DEPO HAZIRLIK LİSTESİ</b>\n"
    report += "--------------------------------\n\n"
    
    # Ürün bazlı gruplama yaparak depocuya kolaylık sağlıyoruz
    summary = {}
    for o in orders_data:
        p_name = o.get("product_name", "Bilinmeyen Ürün")
        summary[p_name] = summary.get(p_name, 0) + o.get("quantity", 0)
    
    for product, qty in summary.items():
        report += f"🔹 {product}: <b>{qty} adet</b>\n"
    
    report += "\n✅ Lütfen ürünleri hazırlayıp kurye rotasına hazır hale getirin."
    return report

def format_courier_report(orders_data: list[dict[str, Any]]) -> str:
    if not orders_data:
        return "🚚 <b>Bugün teslim edilecek sipariş bulunmuyor.</b>"
    
    report = "📍 <b>GÜNLÜK TESLİMAT ROTASI</b>\n"
    report += "--------------------------------\n\n"
    
    for i, o in enumerate(orders_data, 1):
        order_num = o.get("order_number", "N/A")
        address = o.get("address", "Adres Bilgisi Yok")
        customer = o.get("customer_name", "Müşteri")
        report += f"{i}. <b>{order_num}</b> - {customer}\n"
        report += f"🏠 {address}\n\n"
    
    report += "🛣️ İyi yolculuklar, güvenli sürüşler!"
    return report
