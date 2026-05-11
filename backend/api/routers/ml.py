from fastapi import APIRouter, Depends, Query

from core.deps import get_ml_service
from schemas.ml import PriceFeedbackRequest
from services.ml.ml_service import MLService

router = APIRouter()


@router.get("/forecast/{product_id}")
def forecast_demand(
    product_id: int,
    days: int = Query(default=7, ge=1, le=90),
    ml_service: MLService = Depends(get_ml_service),
):
    """Ürün bazında talep tahmini endpoint'i."""
    return ml_service.forecast_demand(product_id=product_id, days=days)


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
