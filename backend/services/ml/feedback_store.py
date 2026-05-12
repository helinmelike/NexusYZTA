from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class FeedbackStore:
    """Fiyat öneri geri bildirimlerini bellekte tutar."""

    _records: list[dict[str, Any]] = []

    def add_feedback(
        self,
        product_id: int,
        suggested_price: float,
        accepted: bool,
        final_price: float | None = None,
    ) -> dict[str, Any]:
        """Yeni geri bildirim kaydı ekler."""
        record = {
            "product_id": product_id,
            "suggested_price": float(round(suggested_price, 2)),
            "accepted": bool(accepted),
            "final_price": float(round(final_price, 2)) if final_price is not None else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._records.append(record)
        return {"success": True, "message": "Geri bildirim kaydedildi.", "data": record}

    def acceptance_rate(self, product_id: int) -> dict[str, Any]:
        """Ürün bazında kabul oranını hesaplar."""
        records = [record for record in self._records if record["product_id"] == product_id]
        if not records:
            data = {"product_id": product_id, "acceptance_rate": 0.0, "total_feedback_count": 0}
            return {"success": True, "message": "Bu ürün için geri bildirim bulunamadı.", "data": data}

        accepted_count = sum(1 for record in records if record["accepted"])
        rate = accepted_count / len(records)
        data = {
            "product_id": product_id,
            "acceptance_rate": float(round(rate, 4)),
            "total_feedback_count": len(records),
        }
        return {"success": True, "message": "Kabul oranı hesaplandı.", "data": data}
