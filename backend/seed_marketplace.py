import sys, os, random
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from database.db import SessionLocal
from database.models.order import Order
from database.models.order_item import OrderItem
from database.models.customer import Customer
from database.models.product import Product

db = SessionLocal()
products = db.query(Product).all()
if not products:
    print('Urun yok')
    db.close()
    sys.exit(1)

trendyol_customers = [
    {'full_name': 'Ayse Kaya', 'phone': '05321234501', 'address': 'Kadikoy Istanbul'},
    {'full_name': 'Mehmet Demir', 'phone': '05334567801', 'address': 'Cankaya Ankara'},
    {'full_name': 'Fatma Yildiz', 'phone': '05345678901', 'address': 'Konak Izmir'},
    {'full_name': 'Ali Sahin', 'phone': '05356789001', 'address': 'Nilufer Bursa'},
    {'full_name': 'Zeynep Celik', 'phone': '05367890101', 'address': 'Muratpasa Antalya'},
]
hepsiburada_customers = [
    {'full_name': 'Selin Ozturk', 'phone': '05411234501', 'address': 'Beylikduzu Istanbul'},
    {'full_name': 'Emre Aydin', 'phone': '05424567801', 'address': 'Mamak Ankara'},
    {'full_name': 'Busra Yilmaz', 'phone': '05435678901', 'address': 'Karsiyaka Izmir'},
    {'full_name': 'Serkan Dogan', 'phone': '05446789001', 'address': 'Osmangazi Bursa'},
]

def get_or_create(data):
    c = db.query(Customer).filter(Customer.phone == data['phone']).first()
    if not c:
        c = Customer(full_name=data['full_name'], phone=data['phone'], address=data['address'])
        db.add(c); db.flush()
    return c

statuses = ['pending','preparing','shipped','delivered','delivered','delivered']

for i in range(40):
    cdata = random.choice(trendyol_customers)
    customer = get_or_create(cdata)
    chosen = random.sample(products, min(random.randint(1,3), len(products)))
    total = 0
    order = Order(customer_id=customer.id, status=random.choice(statuses), channel='trendyol',
        created_at=datetime.now()-timedelta(minutes=random.randint(0,60*24*60)), total_amount=0)
    db.add(order); db.flush()
    for p in chosen:
        qty = random.randint(1,4)
        total += float(p.price)*qty
        db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=float(p.price)))
    order.total_amount = round(total,2)

for i in range(25):
    cdata = random.choice(hepsiburada_customers)
    customer = get_or_create(cdata)
    chosen = random.sample(products, min(random.randint(1,2), len(products)))
    total = 0
    order = Order(customer_id=customer.id, status=random.choice(statuses), channel='hepsiburada',
        created_at=datetime.now()-timedelta(minutes=random.randint(0,45*24*60)), total_amount=0)
    db.add(order); db.flush()
    for p in chosen:
        qty = random.randint(1,3)
        total += float(p.price)*qty
        db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=float(p.price)))
    order.total_amount = round(total,2)

db.commit(); db.close()
print('Tamamlandi: 40 Trendyol + 25 Hepsiburada siparisi eklendi')
