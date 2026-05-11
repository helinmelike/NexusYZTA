from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol

from database.models.product import Product
from services.ml.demand_forecaster import DemandForecaster
from services.ml.feedback_store import FeedbackStore
from services.ml.price_advisor import PriceAdvisor


class OrderRepositoryProtocol(Protocol):
    """ML katmanının ihtiyaç duyduğu repository sözleşmesi."""

    db: Any

    def get_all(self) -> list[Any]:
        ...


class MLService:
    """Tahmin, fiyat önerisi ve geri bildirim süreçlerini yöneten facade sınıfı."""

    def __init__(
        self,
        repo: OrderRepositoryProtocol,
        forecaster: DemandForecaster | None = None,
        advisor: PriceAdvisor | None = None,
        feedback_store: FeedbackStore | None = None,
    ):
        self._repo = repo
        self._forecaster = forecaster or DemandForecaster()
        self._advisor = advisor or PriceAdvisor()
        self._feedback_store = feedback_store or FeedbackStore()

    def forecast_demand(self, product_id: int, days: int) -> dict[str, Any]:
        """Ürün bazında ileriye dönük talep tahmini üretir."""
        if product_id <= 0:
            return {"success": False, "message": "Geçersiz product_id.", "data": None}

        orders = self._repo.get_all()
        aggregated_by_order = defaultdict(int)

        for order in orders:
            for item in getattr(order, "items", []):
                if item.product_id == product_id:
                    aggregated_by_order[int(order.id)] += int(item.quantity or 0)

        historical_quantities = [
            quantity for _, quantity in sorted(aggregated_by_order.items(), key=lambda pair: pair[0])
        ]
        forecast_result = self._forecaster.forecast(historical_quantities, days)
        if not forecast_result["success"]:
            return forecast_result

        forecast_result["data"]["product_id"] = product_id
        forecast_result["data"]["historical_points"] = len(historical_quantities)
        return forecast_result

    def suggest_price(
        self,
        product_id: int,
        low_stock_threshold: int = 20,
        high_stock_threshold: int = 100,
    ) -> dict[str, Any]:
        """Ürün stok/fiyat bilgisine göre yeni fiyat önerir."""
        product = self._repo.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Ürün bulunamadı.", "data": None}

        suggestion = self._advisor.suggest(
            current_price=float(product.price),
            stock_quantity=int(product.stock_quantity or 0),
            low_stock_threshold=low_stock_threshold,
            high_stock_threshold=high_stock_threshold,
        )
        if not suggestion["success"]:
            return suggestion

        suggestion["data"]["product_id"] = product_id
        suggestion["data"]["product_name"] = product.name
        return suggestion

    def submit_feedback(
        self,
        product_id: int,
        suggested_price: float,
        accepted: bool,
        strategy: str,
        final_price: float | None = None,
    ) -> dict[str, Any]:
        """Fiyat önerisi geri bildirimi kaydeder ve öğrenme oranlarını günceller."""
        store_result = self._feedback_store.add_feedback(
            product_id=product_id,
            suggested_price=suggested_price,
            accepted=accepted,
            final_price=final_price,
        )
        if not store_result["success"]:
            return store_result

        learn_result = self._advisor.learn(strategy=strategy, accepted=accepted)
        if not learn_result["success"]:
            return learn_result

        acceptance = self._feedback_store.acceptance_rate(product_id)
        if not acceptance["success"]:
            return acceptance

        return {
            "success": True,
            "message": "Feedback kaydedildi ve model oranları güncellendi.",
            "data": {
                "feedback": store_result["data"],
                "rates": learn_result["data"],
                "acceptance": acceptance["data"],
            },
        }
