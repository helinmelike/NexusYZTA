"""Product and stock service layer."""

from contextlib import contextmanager
from typing import Any

from database.db import SessionLocal
from database.models.inventory_movement import InventoryMovement
from database.models.product import Product


LOW_STOCK_THRESHOLD = 20


@contextmanager
def _session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _serialize_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "stock_quantity": int(product.stock_quantity or 0),
    }


def list_products() -> dict[str, Any]:
    with _session_scope() as db:
        products = db.query(Product).order_by(Product.id.asc()).all()
        return {"success": True, "message": "Products fetched", "data": [_serialize_product(p) for p in products]}


def get_product(product_id: int) -> dict[str, Any]:
    with _session_scope() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Product not found", "data": None}
        return {"success": True, "message": "Product fetched", "data": _serialize_product(product)}


def check_stock(product_id: int) -> dict[str, Any]:
    with _session_scope() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Product not found", "data": None}
        stock = int(product.stock_quantity or 0)
        return {
            "success": True,
            "message": "Stock fetched",
            "data": {
                "product_id": product.id,
                "product_name": product.name,
                "stock_quantity": stock,
                "is_low_stock": stock <= LOW_STOCK_THRESHOLD,
            },
        }


def low_stock_products(threshold: int = LOW_STOCK_THRESHOLD) -> dict[str, Any]:
    safe_threshold = max(0, int(threshold))
    with _session_scope() as db:
        products = (
            db.query(Product)
            .filter(Product.stock_quantity <= safe_threshold)
            .order_by(Product.stock_quantity.asc(), Product.id.asc())
            .all()
        )
        return {"success": True, "message": "Low stock products fetched", "data": [_serialize_product(p) for p in products]}


def update_stock(product_id: int, quantity_change: int, note: str | None = None) -> dict[str, Any]:
    delta = int(quantity_change)
    with _session_scope() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Product not found", "data": None}
        current_stock = int(product.stock_quantity or 0)
        new_stock = current_stock + delta
        if new_stock < 0:
            return {"success": False, "message": "Insufficient stock for this operation", "data": None}
        product.stock_quantity = new_stock
        movement_type = "in" if delta >= 0 else "out"
        db.add(InventoryMovement(
            product_id=product.id,
            movement_type=movement_type,
            quantity=abs(delta),
            note=note or "Stock updated via service",
        ))
        return {
            "success": True,
            "message": "Stock updated",
            "data": {
                "product_id": product.id,
                "product_name": product.name,
                "previous_stock": current_stock,
                "new_stock": new_stock,
                "quantity_change": delta,
                "movement_type": movement_type,
            },
        }


def update_price(product_id: int, new_price: float) -> dict[str, Any]:
    """Ürün fiyatını günceller."""
    if new_price <= 0:
        return {"success": False, "message": "Fiyat 0'dan büyük olmalıdır", "data": None}
    with _session_scope() as db:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Product not found", "data": None}
        old_price = float(product.price)
        product.price = new_price
        return {
            "success": True,
            "message": "Price updated",
            "data": {
                "product_id": product.id,
                "product_name": product.name,
                "previous_price": old_price,
                "new_price": float(new_price),
            },
        }


def add_product(name: str, price: float, stock_quantity: int = 0) -> dict[str, Any]:
    """Yeni ürün ekler."""
    with _session_scope() as db:
        existing = db.query(Product).filter(Product.name == name).first()
        if existing:
            return {"success": False, "message": "Bu isimde ürün zaten var", "data": _serialize_product(existing)}
        product = Product(name=name, price=price, stock_quantity=stock_quantity)
        db.add(product)
        db.flush()
        db.refresh(product)
        return {"success": True, "message": "Product created", "data": _serialize_product(product)}