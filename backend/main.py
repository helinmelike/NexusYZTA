from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from services.workflow_service import start_workflow_task
from api.routers import cargo, orders, customers, agent, products
import logging

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kooperatif Yönetim Sistemi")

# Scheduler Kurulumu
scheduler = BackgroundScheduler()
# Her gün sabah 08:00'de çalışır
scheduler.add_job(start_workflow_task, 'cron', hour=8, minute=0)
# Test için: Her 1 dakikada bir çalıştır (görmek istersen alttaki satırı aktif et)
# scheduler.add_job(start_workflow_task, 'interval', minutes=1)

@app.on_event("startup")
def startup_event():
    scheduler.start()
    logger.info("Scheduler started...")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shut down...")

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