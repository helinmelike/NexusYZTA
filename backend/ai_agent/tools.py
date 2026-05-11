from langchain_core.tools import tool

from services.product_service import (
    list_products, get_product, check_stock, low_stock_products, update_stock,
)
from services.order_service import (
    get_order_by_id, get_customer_orders, cancel_order,
    list_recent_orders, get_order_detail, create_order,
)
from services.customer_service import (
    get_customer, find_customer_by_phone, create_customer, customer_statistics,
)
from services.cargo_service import (
    track_cargo, get_estimated_delivery, update_cargo_status, get_cargo_status,
)

import openpyxl, os
from database.db import SessionLocal
from database.models.product import Product
from database.models.customer import Customer
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.inventory_movement import InventoryMovement
from sqlalchemy.orm import joinedload


@tool
def tool_list_products(_: str = "") -> str:
    """Tüm ürünleri listeler. Kullanım: 'ürünleri listele', 'ürünleri göster'"""
    result = list_products()
    if not result["success"]:
        return result["message"]
    products = result["data"]
    if not products:
        return "Hiç ürün bulunamadı."
    lines = [f"{'ID':<5} {'Ürün Adı':<25} {'Fiyat':>10} {'Stok':>8}"]
    lines.append("-" * 52)
    for p in products:
        lines.append(f"{p['id']:<5} {p['name']:<25} {p['price']:>9.2f}₺ {p['stock_quantity']:>7}")
    return "\n".join(lines)


@tool
def tool_check_stock(product_id: int) -> str:
    """Belirli bir ürünün stok durumunu kontrol eder."""
    result = check_stock(product_id)
    if not result["success"]:
        return result["message"]
    d = result["data"]
    durum = "⚠️ Düşük stok!" if d["is_low_stock"] else "✅ Stok yeterli"
    return f"Ürün: {d['product_name']}\nStok: {d['stock_quantity']} adet\nDurum: {durum}"


@tool
def tool_low_stock_products(threshold: int = 20) -> str:
    """Stoğu kritik seviyenin altındaki ürünleri listeler."""
    result = low_stock_products(threshold)
    if not result["success"]:
        return result["message"]
    products = result["data"]
    if not products:
        return f"✅ Tüm ürünlerin stoğu {threshold} adetten fazla."
    lines = [f"⚠️ Kritik stok (eşik: {threshold}):"]
    for p in products:
        lines.append(f"  • {p['name']} — {p['stock_quantity']} adet")
    return "\n".join(lines)


@tool
def tool_update_stock(product_id: int, quantity_change: int, note: str = "") -> str:
    """Ürün stoğunu günceller. Pozitif ekler, negatif düşürür."""
    result = update_stock(product_id, quantity_change, note or None)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    ok = "➕" if quantity_change > 0 else "➖"
    return f"{ok} '{d['product_name']}' stoğu güncellendi.\nÖnceki: {d['previous_stock']} → Yeni: {d['new_stock']}"


@tool
def tool_update_price(product_id: int, new_price: float) -> str:
    """
    Ürün fiyatını günceller.
    Kullanım: 'domates salçasının fiyatını 160 tl yap', 'ürün 1 fiyatı 200 olsun'
    """
    from services.product_service import update_price
    result = update_price(product_id, new_price)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    return f"✅ '{d['product_name']}' fiyatı güncellendi.\nÖnceki: {d['previous_price']:.2f}₺ → Yeni: {d['new_price']:.2f}₺"


@tool
def tool_add_product(name: str, price: float, stock_quantity: int = 0) -> str:
    """
    Yeni ürün ekler. Fiyat mutlaka belirtilmelidir, 0 olamaz.
    Kullanım: 'yeni ürün ekle: zeytinyağı 180 tl 50 adet'
    Eğer kullanıcı fiyat belirtmediyse, fiyatı sormadan ekleme yapma.
    """
    from services.product_service import add_product as _add_product
    result = _add_product(name, price, stock_quantity)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    return f"✅ '{d['name']}' eklendi. ID: {d['id']} | Fiyat: {d['price']:.2f}₺ | Stok: {d['stock_quantity']}"


@tool
def tool_delete_product(product_id: int) -> str:
    """
    Ürünü sistemden kalıcı olarak siler.
    Kullanım: 'ürün 7yi sil', 'gül suyunu kaldır', 'ID 6 olan ürünü sil'
    """
    from services.product_service import delete_product
    result = delete_product(product_id)
    if not result["success"]:
        return f"❌ {result['message']}"
    return f"✅ '{result['data']['name']}' başarıyla silindi."


@tool
def tool_list_recent_orders(limit: int = 10) -> str:
    """Son siparişleri listeler."""
    result = list_recent_orders(limit)
    if not result["success"]:
        return result["message"]
    orders = result["data"]
    if not orders:
        return "Henüz sipariş bulunmuyor."
    lines = [f"{'ID':<6} {'Müşteri':<20} {'Durum':<12} {'Toplam':>10}"]
    lines.append("-" * 52)
    for o in orders:
        lines.append(f"#{o['id']:<5} {o['customer_name'] or '-':<20} {o['status']:<12} {o['total_amount']:>9.2f}₺")
    return "\n".join(lines)


@tool
def tool_get_order_detail(order_id: int) -> str:
    """Sipariş detayını gösterir."""
    result = get_order_detail(order_id)
    if not result["success"]:
        return f"❌ {result['message']}"
    o = result["data"]
    lines = [f"📦 Sipariş #{o['id']}", f"Müşteri: {o['customer_name']}", f"Durum: {o['status']}", f"Toplam: {o['total_amount']:.2f}₺", "", "Ürünler:"]
    for item in o.get("items", []):
        lines.append(f"  • {item['product_name']} x{item['quantity']} @ {item['unit_price']:.2f}₺ = {item['line_total']:.2f}₺")
    return "\n".join(lines)


@tool
def tool_get_customer_orders(customer_id: int) -> str:
    """Bir müşterinin tüm siparişlerini listeler."""
    result = get_customer_orders(customer_id)
    if not result["success"]:
        return f"❌ {result['message']}"
    orders = result["data"]
    if not orders:
        return "Bu müşteriye ait sipariş bulunamadı."
    lines = [f"{'ID':<6} {'Durum':<12} {'Toplam':>10}"]
    for o in orders:
        lines.append(f"#{o['id']:<5} {o['status']:<12} {o['total_amount']:>9.2f}₺")
    return "\n".join(lines)


@tool
def tool_update_order_status(order_id: int, new_status: str) -> str:
    """Sipariş durumunu günceller. Geçerli: pending, preparing, shipped, delivered, cancelled"""
    result = update_cargo_status(order_id, new_status)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    return f"✅ Sipariş #{d['order_id']} → {d['order_status']}\nTakip no: {d['tracking_number']}"


@tool
def tool_cancel_order(order_id: int) -> str:
    """Siparişi iptal eder. Stoklar otomatik iade edilir."""
    result = cancel_order(order_id)
    if not result["success"]:
        return f"❌ {result['message']}"
    return f"✅ Sipariş #{result['data']['id']} iptal edildi. Stoklar iade edildi."


@tool
def tool_find_customer(phone: str) -> str:
    """Telefon numarasıyla müşteri bulur."""
    result = find_customer_by_phone(phone)
    if not result["success"]:
        return f"❌ {result['message']}"
    c = result["data"]
    return f"👤 {c['full_name']}\nID: {c['id']} | Tel: {c['phone']} | Adres: {c['address']}"


@tool
def tool_customer_statistics(customer_id: int) -> str:
    """Müşteri istatistiklerini gösterir."""
    result = customer_statistics(customer_id)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    c = d["customer"]
    sb = d["status_breakdown"]
    return f"📊 {c['full_name']}\nToplam sipariş: {d['total_orders']}\nToplam harcama: {d['total_spent']:.2f}₺\nKargoda: {sb['shipped']} | Bekleyen: {sb['pending']}"


@tool
def tool_create_customer(full_name: str, phone: str, address: str = "") -> str:
    """Yeni müşteri oluşturur."""
    result = create_customer(full_name, phone, address)
    if not result["success"]:
        return f"❌ {result['message']}"
    c = result["data"]
    return f"✅ '{c['full_name']}' eklendi. ID: {c['id']} | Tel: {c['phone']}"


@tool
def tool_track_cargo(tracking_number: str) -> str:
    """Kargo takip numarasıyla kargo durumunu sorgular."""
    result = track_cargo(tracking_number)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    return f"📦 Takip No: {d['tracking_number']}\nSipariş: {d['order_status']} | Kargo: {d['cargo_status']}"


@tool
def tool_get_estimated_delivery(tracking_number: str) -> str:
    """Tahmini teslimat tarihini hesaplar."""
    result = get_estimated_delivery(tracking_number)
    if not result["success"]:
        return f"❌ {result['message']}"
    d = result["data"]
    return f"🚚 {d['tracking_number']}\nKargo: {d['cargo_status']}\nTahmini teslimat: {d['estimated_delivery_date']}"


@tool
def tool_export_to_excel(table: str) -> str:
    """
    Verileri Excel dosyasına aktarır.
    table: 'products', 'orders', 'customers', 'inventory'
    """
    db = SessionLocal()
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        if table == "products":
            ws.title = "Ürünler"
            ws.append(["ID", "Ürün Adı", "Fiyat (₺)", "Stok Miktarı"])
            for p in db.query(Product).all():
                ws.append([p.id, p.name, p.price, p.stock_quantity])
        elif table == "orders":
            ws.title = "Siparişler"
            ws.append(["Sipariş ID", "Müşteri", "Telefon", "Durum", "Toplam (₺)", "Ürünler"])
            orders = db.query(Order).options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product)).all()
            for o in orders:
                urunler = ", ".join([f"{i.product.name} x{i.quantity}" for i in o.items])
                ws.append([o.id, o.customer.full_name, o.customer.phone, o.status, o.total_amount, urunler])
        elif table == "customers":
            ws.title = "Müşteriler"
            ws.append(["ID", "Ad Soyad", "Telefon", "Adres"])
            for c in db.query(Customer).all():
                ws.append([c.id, c.full_name, c.phone, c.address])
        elif table == "inventory":
            ws.title = "Envanter"
            ws.append(["ID", "Ürün", "Hareket Tipi", "Miktar", "Not"])
            for h in db.query(InventoryMovement).options(joinedload(InventoryMovement.product)).all():
                ws.append([h.id, h.product.name, h.movement_type, h.quantity, h.note])
        else:
            return f"❌ Geçersiz tablo: '{table}'. Geçerli: products, orders, customers, inventory"
        os.makedirs("exports", exist_ok=True)
        path = os.path.join("exports", f"{table}.xlsx")
        wb.save(path)
        return f"✅ Excel oluşturuldu: {path}"
    finally:
        db.close()


all_tools = [
    tool_list_products,
    tool_check_stock,
    tool_low_stock_products,
    tool_update_stock,
    tool_update_price,
    tool_add_product,
    tool_delete_product,
    tool_list_recent_orders,
    tool_get_order_detail,
    tool_get_customer_orders,
    tool_update_order_status,
    tool_cancel_order,
    tool_find_customer,
    tool_customer_statistics,
    tool_create_customer,
    tool_track_cargo,
    tool_get_estimated_delivery,
    tool_export_to_excel,
]