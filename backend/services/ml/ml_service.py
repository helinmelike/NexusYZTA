from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Protocol

from database.models.product import Product
from services.ml.demand_forecaster import DemandForecaster
from services.ml.feedback_store import FeedbackStore
from services.ml.price_advisor import PriceAdvisor


class OrderRepositoryProtocol(Protocol):
    db: Any

    def get_all(self) -> list[Any]: ...
    def get_orders_after(self, cutoff: datetime) -> list[Any]: ...


class ProductRepositoryProtocol(Protocol):
    def get_by_id(self, id: int) -> Any: ...


class MLService:
    def __init__(
        self,
        repo: OrderRepositoryProtocol,
        product_repo: ProductRepositoryProtocol | None = None,
        forecaster: DemandForecaster | None = None,
        advisor: PriceAdvisor | None = None,
        feedback_store: FeedbackStore | None = None,
    ):
        self._repo         = repo
        self._product_repo = product_repo
        self._forecaster   = forecaster or DemandForecaster()
        self._advisor      = advisor or PriceAdvisor()
        self._feedback_store = feedback_store or FeedbackStore()

    # ── mevcut metodlar (değişmedi) ──────────────────────────────

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
            qty for _, qty in sorted(aggregated_by_order.items())
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

    # ── yeni metodlar (sınıf içinde, girintiye dikkat) ───────────

    def get_top_products(self, top_n: int = 5, days_back: int = 90) -> dict:
        """Son N günün satışına göre en çok satılması beklenen ürünleri döndür."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        orders = self._repo.get_orders_after(cutoff)
        product_sales: dict[int, list] = defaultdict(list)
        for order in orders:
            for item in getattr(order, "items", []):
                product_sales[item.product_id].append({
                    "date": order.created_at,
                    "quantity": item.quantity,
                })

        scored = []
        for product_id, sales in product_sales.items():
            velocity   = self._calc_velocity(sales)
            trend      = self._calc_trend(sales)
            quantities = [s["quantity"] for s in sales]
            forecast   = self._forecaster.forecast(quantities, days=7)
            product = self._product_repo.get_by_id(product_id)
            prediction = (
            forecast["data"]["total_predicted_demand"]
            if forecast["success"]
            else 0.0
            )
            stock_risk = self._calc_stock_risk(product_id, prediction)

            scored.append({
                "product_id":             product_id,
                "velocity":               round(velocity, 2),
                "trend":                  trend,
                "predicted_weekly_demand": round(prediction, 1),
                "stock_risk":             stock_risk,
                "score":                  round(
                    velocity * 0.4 + (1.0 if trend == "up" else 0.0) * 0.4, 2
                ),
                "product_name": product.name if product else None,
            })

        top = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
        return {"success": True, "data": top, "period_days": days_back}

    def check_stock_alerts(self, top_n: int = 5) -> dict:
        """Stok riski olan ürünler için uyarı üret."""
        result = self.get_top_products(top_n)
        alerts = [
            {
                "product_id":       p["product_id"],
                "predicted_demand": p["predicted_weekly_demand"],
                "risk":             p["stock_risk"],
                "message": (
                    f"Ürün {p['product_id']}: haftalık tahmini talep "
                    f"{p['predicted_weekly_demand']} adet — stok {p['stock_risk']}"
                ),
            }
            for p in result["data"]
            if p["stock_risk"] in ("critical", "warning")
        ]

        if alerts:
            from notifications.email_service import EmailService
            #EmailService().send_stock_alert(alerts)

        return {"success": True, "alerts": alerts, "count": len(alerts)}

    # ── yardımcı metodlar ────────────────────────────────────────

    def _calc_velocity(self, sales: list) -> float:
        return sum(s["quantity"] for s in sales) / max(len(sales), 1)

    def _calc_trend(self, sales: list) -> str:
        if len(sales) < 6:
            return "stable"
        quantities = [s["quantity"] for s in sales]
        mid        = len(quantities) // 2
        first_half  = sum(quantities[:mid])
        second_half = sum(quantities[mid:])
        if second_half > first_half * 1.1:
            return "up"
        if second_half < first_half * 0.9:
            return "down"
        return "stable"

    def _calc_stock_risk(self, product_id: int, predicted_demand: float) -> str:
        if not self._product_repo:
            return "unknown"
        products = {
            p.id: p for p in self._product_repo.get_all()
        }
        product = products.get(product_id)
        if not product:
            return "unknown"
        ratio = predicted_demand / max(product.stock_quantity, 1)
        if ratio > 1.5:
            return "critical"
        if ratio > 0.8:
            return "warning"
        return "ok"