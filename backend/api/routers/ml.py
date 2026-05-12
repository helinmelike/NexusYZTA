from fastapi import APIRouter, Depends, Query

from core.deps import get_ml_service
from schemas.ml import PriceFeedbackRequest
from services.ml.ml_service import MLService
from functools import lru_cache
from typing import Any, Dict
from collections import defaultdict  
router = APIRouter()


@router.get("/forecast/{product_id}")
def forecast_demand(
    product_id: int,
    days: int = 7,
    ml_service: MLService = Depends(get_ml_service),
):
    if product_id <= 0:
        return {
            "success": False,
            "message": "Geçersiz product_id.",
            "data": None
        }

    # cache (opsiyonel - MLService içine taşınmalı aslında)
    cache_key = f"{product_id}:{days}"

    if hasattr(ml_service, "_forecast_cache"):
        if cache_key in ml_service._forecast_cache:
            return ml_service._forecast_cache[cache_key]

    orders = ml_service._repo.get_all()

    aggregated_by_order = defaultdict(int)

    for order in orders:
        for item in getattr(order, "items", []):
            if item.product_id == product_id:
                aggregated_by_order[int(order.id)] += int(item.quantity or 0)

    historical_quantities = [
        qty for _, qty in sorted(aggregated_by_order.items())
    ]

    forecast_result = ml_service._forecaster.forecast(
        historical_quantities,
        days
    )

    if not forecast_result["success"]:
        return forecast_result

    data = forecast_result["data"]
    data["product_id"] = product_id
    data["historical_points"] = len(historical_quantities)

    result = {
        "success": True,
        "message": "Talep tahmini başarıyla oluşturuldu.",
        "data": data
    }

    if hasattr(ml_service, "_forecast_cache"):
        ml_service._forecast_cache[cache_key] = result

    return result

@router.get("/price-suggest/{product_id}")
def suggest_price(
    product_id: int,
    low_stock_threshold: int = Query(default=20, ge=0),
    high_stock_threshold: int = Query(default=100, ge=1),
    ml_service: MLService = Depends(get_ml_service),
):
    """Ürün için fiyat önerisi endpoint'i."""
    return ml_service.suggest_price(
        product_id=product_id,
        low_stock_threshold=low_stock_threshold,
        high_stock_threshold=high_stock_threshold,
    )


@router.post("/feedback")
def submit_feedback(
    payload: PriceFeedbackRequest,
    ml_service: MLService = Depends(get_ml_service),
):
    """Fiyat önerisi geri bildirim endpoint'i."""
    return ml_service.submit_feedback(
        product_id=payload.product_id,
        suggested_price=payload.suggested_price,
        accepted=payload.accepted,
        strategy=payload.strategy,
        final_price=payload.final_price,
    )

@router.get("/top-products")
def top_products(
    top_n: int = 5,
    days_back: int = 90,
    svc: MLService = Depends(get_ml_service),
):
    """Son N günün verisine göre en çok satılması beklenen ürünler."""
    return svc.get_top_products(top_n, days_back)


@router.get("/stock-alerts")
def stock_alerts(
    top_n: int = 5,
    svc: MLService = Depends(get_ml_service),
):
    """Stok riski olan ürünler için yönetici uyarısı."""
    return svc.check_stock_alerts(top_n)