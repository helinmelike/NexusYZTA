from core.config import settings
print("DATABASE_URL:", settings.database_url)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import cargo, orders, customers, agent, products

app = FastAPI(title="Kooperatif Yönetim Sistemi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cargo.router,     prefix="/cargo",     tags=["cargo"])
app.include_router(orders.router,    prefix="/orders",    tags=["orders"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router,  prefix="/products",  tags=["products"])
app.include_router(agent.router,     prefix="/agent",     tags=["agent"])