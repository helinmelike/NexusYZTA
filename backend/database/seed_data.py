from sqlalchemy.orm import joinedload

from database.db import SessionLocal
from database.models.customer import Customer
from database.models.inventory_movement import InventoryMovement
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.product import Product


def get_or_create_product(db, name, price, stock_quantity):
    product = db.query(Product).filter(Product.name == name).first()
    if product:
        return product

    product = Product(name=name, price=price, stock_quantity=stock_quantity)
    db.add(product)
    db.flush()
    return product


def get_or_create_customer(db, full_name, phone, address):
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if customer:
        return customer

    customer = Customer(full_name=full_name, phone=phone, address=address)
    db.add(customer)
    db.flush()
    return customer


def order_exists(db, customer_id, status, total_amount, items):
    candidates = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(
            Order.customer_id == customer_id,
            Order.status == status,
            Order.total_amount == total_amount,
        )
        .all()
    )

    normalized_items = sorted(
        [{"product_id": i["product_id"], "quantity": i["quantity"], "unit_price": i["unit_price"]} for i in items],
        key=lambda x: (x["product_id"], x["quantity"], x["unit_price"]),
    )

    for order in candidates:
        existing_items = sorted(
            [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in order.items
            ],
            key=lambda x: (x["product_id"], x["quantity"], x["unit_price"]),
        )
        if existing_items == normalized_items:
            return True

    return False


def add_inventory_movement_if_missing(db, product_id, movement_type, quantity, note):
    movement = (
        db.query(InventoryMovement)
        .filter(
            InventoryMovement.product_id == product_id,
            InventoryMovement.movement_type == movement_type,
            InventoryMovement.quantity == quantity,
            InventoryMovement.note == note,
        )
        .first()
    )
    if movement:
        return

    db.add(
        InventoryMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            note=note,
        )
    )


def seed_data():
    db = SessionLocal()
    try:
        products_data = [
            {"name": "Domates Salçası", "price": 145.0, "stock_quantity": 120},
            {"name": "Organik Bal", "price": 260.0, "stock_quantity": 80},
            {"name": "Ev Yapımı Reçel", "price": 115.0, "stock_quantity": 95},
            {"name": "Tarhana", "price": 98.0, "stock_quantity": 150},
            {"name": "Erişte", "price": 72.0, "stock_quantity": 170},
        ]

        customers_data = [
            {
                "full_name": "Ayse Kaya",
                "phone": "05320000001",
                "address": "Ataturk Mah. Cumhuriyet Cad. No:12 Izmir",
            },
            {
                "full_name": "Mehmet Demir",
                "phone": "05320000002",
                "address": "Yildirim Beyazit Sok. No:8 Bursa",
            },
            {
                "full_name": "Fatma Celik",
                "phone": "05320000003",
                "address": "Baglarbasi Mah. Sehitler Cad. No:24 Ankara",
            },
        ]

        products_by_name = {}
        for p in products_data:
            product = get_or_create_product(db, p["name"], p["price"], p["stock_quantity"])
            products_by_name[p["name"]] = product

        customers_by_phone = {}
        for c in customers_data:
            customer = get_or_create_customer(db, c["full_name"], c["phone"], c["address"])
            customers_by_phone[c["phone"]] = customer

        db.flush()

        orders_data = [
            {
                "customer_phone": "05320000001",
                "status": "pending",
                "items": [
                    {"product_name": "Domates Salçası", "quantity": 2},
                    {"product_name": "Tarhana", "quantity": 1},
                ],
            },
            {
                "customer_phone": "05320000002",
                "status": "preparing",
                "items": [
                    {"product_name": "Organik Bal", "quantity": 1},
                    {"product_name": "Erişte", "quantity": 3},
                ],
            },
            {
                "customer_phone": "05320000003",
                "status": "shipped",
                "items": [
                    {"product_name": "Ev Yapımı Reçel", "quantity": 2},
                    {"product_name": "Domates Salçası", "quantity": 1},
                    {"product_name": "Erişte", "quantity": 1},
                ],
            },
        ]

        for order_data in orders_data:
            customer = customers_by_phone[order_data["customer_phone"]]
            prepared_items = []
            total_amount = 0.0

            for item in order_data["items"]:
                product = products_by_name[item["product_name"]]
                unit_price = product.price
                quantity = item["quantity"]
                total_amount += unit_price * quantity
                prepared_items.append(
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    }
                )

            if order_exists(
                db=db,
                customer_id=customer.id,
                status=order_data["status"],
                total_amount=total_amount,
                items=prepared_items,
            ):
                continue

            order = Order(
                customer_id=customer.id,
                status=order_data["status"],
                total_amount=total_amount,
            )
            db.add(order)
            db.flush()

            for pi in prepared_items:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=pi["product_id"],
                        quantity=pi["quantity"],
                        unit_price=pi["unit_price"],
                    )
                )

        inventory_data = [
            {"product_name": "Domates Salçası", "movement_type": "in", "quantity": 120, "note": "Ilk stok girisi"},
            {"product_name": "Organik Bal", "movement_type": "in", "quantity": 80, "note": "Ilk stok girisi"},
            {"product_name": "Ev Yapımı Reçel", "movement_type": "in", "quantity": 95, "note": "Ilk stok girisi"},
            {"product_name": "Tarhana", "movement_type": "in", "quantity": 150, "note": "Ilk stok girisi"},
            {"product_name": "Erişte", "movement_type": "in", "quantity": 170, "note": "Ilk stok girisi"},
            {"product_name": "Domates Salçası", "movement_type": "out", "quantity": 3, "note": "Ornek siparis cikisi"},
            {"product_name": "Organik Bal", "movement_type": "out", "quantity": 1, "note": "Ornek siparis cikisi"},
        ]

        for m in inventory_data:
            product = products_by_name[m["product_name"]]
            add_inventory_movement_if_missing(
                db=db,
                product_id=product.id,
                movement_type=m["movement_type"],
                quantity=m["quantity"],
                note=m["note"],
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
    print("Seed data başarıyla eklendi.")
