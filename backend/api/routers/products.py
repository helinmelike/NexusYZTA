from fastapi import APIRouter
from services.product_service import (
    list_products, get_product, check_stock,
    low_stock_products, update_stock, add_product, delete_product
)

router = APIRouter()


@router.get("/")
def get_products():
    return list_products()


@router.get("/low-stock")
def get_low_stock():
    return low_stock_products()


@router.get("/{product_id}")
def get_product_by_id(product_id: int):
    return get_product(product_id)


@router.get("/{product_id}/stock")
def get_stock(product_id: int):
    return check_stock(product_id)


@router.patch("/{product_id}/stock")
def patch_stock(product_id: int, body: dict):
    return update_stock(product_id, body.get("quantity_change", 0), body.get("note", ""))


@router.post("/")
def create_product(body: dict):
    return add_product(
        name=body.get("name", ""),
        price=float(body.get("price", 0)),
        stock_quantity=int(body.get("stock_quantity", 0))
    )


@router.delete("/{product_id}")
def remove_product(product_id: int):
    return delete_product(product_id)