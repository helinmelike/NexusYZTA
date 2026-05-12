from __future__ import annotations

from typing import Any


class PriceAdvisor:
    """Stok durumuna göre fiyat önerisi üretir ve geri bildirimle oranları günceller."""

    def __init__(self, markup_rate: float = 0.10, discount_rate: float = 0.10, learning_rate: float = 0.02):
        self._markup_rate = markup_rate
        self._discount_rate = discount_rate
        self._learning_rate = learning_rate

    def suggest(
        self,
        current_price: float,
        stock_quantity: int,
        low_stock_threshold: int,
        high_stock_threshold: int,
    ) -> dict[str, Any]:
        """Stok seviyesine göre fiyat önerisi oluşturur."""
        if current_price <= 0:
            return {"success": False, "message": "current_price sıfırdan büyük olmalıdır.", "data": None}
        if low_stock_threshold < 0 or high_stock_threshold < 0:
            return {"success": False, "message": "Stok eşikleri negatif olamaz.", "data": None}
        if low_stock_threshold >= high_stock_threshold:
            return {"success": False, "message": "low_stock_threshold, high_stock_threshold değerinden küçük olmalıdır.", "data": None}

        if stock_quantity <= low_stock_threshold:
            strategy = "increase"
            rate = self._markup_rate
            suggested_price = current_price * (1 + rate)
            reason = "Stok düşük olduğu için fiyat artırımı önerildi."
        elif stock_quantity >= high_stock_threshold:
            strategy = "decrease"
            rate = self._discount_rate
            suggested_price = current_price * (1 - rate)
            reason = "Stok yüksek olduğu için fiyat indirimi önerildi."
        else:
            strategy = "keep"
            rate = 0.0
            suggested_price = current_price
            reason = "Stok dengeli olduğu için fiyat sabit tutuldu."

        data = {
            "strategy": strategy,
            "current_price": float(round(current_price, 2)),
            "suggested_price": float(round(max(suggested_price, 0.0), 2)),
            "applied_rate": float(round(rate, 4)),
            "stock_quantity": stock_quantity,
            "low_stock_threshold": low_stock_threshold,
            "high_stock_threshold": high_stock_threshold,
            "reason": reason,
        }
        return {"success": True, "message": "Fiyat önerisi oluşturuldu.", "data": data}

    def learn(self, strategy: str, accepted: bool) -> dict[str, Any]:
        """Kullanıcı geri bildirimine göre oranları çevrim içi günceller."""
        if strategy not in {"increase", "decrease", "keep"}:
            return {"success": False, "message": "Geçersiz strategy değeri.", "data": None}

        if strategy == "increase":
            self._markup_rate = self._adjust_rate(self._markup_rate, accepted)
        elif strategy == "decrease":
            self._discount_rate = self._adjust_rate(self._discount_rate, accepted)

        return {
            "success": True,
            "message": "Öneri geri bildirimi işlendi.",
            "data": {
                "markup_rate": float(round(self._markup_rate, 4)),
                "discount_rate": float(round(self._discount_rate, 4)),
                "learning_rate": float(round(self._learning_rate, 4)),
            },
        }

    def _adjust_rate(self, rate: float, accepted: bool) -> float:
        if accepted:
            return min(rate + self._learning_rate, 0.50)
        return max(rate - self._learning_rate, 0.01)
