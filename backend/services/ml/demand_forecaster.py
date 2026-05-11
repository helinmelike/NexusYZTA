from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


class DemandForecaster:
    """Sipariş geçmişinden ürün talebi tahmini üretir."""

    def forecast(self, historical_quantities: list[int], days: int) -> dict[str, Any]:
        """Verilen geçmiş adetlere göre ileriye dönük talep tahmini yapar."""
        if days < 1:
            return {"success": False, "message": "days en az 1 olmalıdır.", "data": None}

        if not historical_quantities:
            daily_predictions = [{"day": day, "predicted_quantity": 0.0} for day in range(1, days + 1)]
            return {
                "success": True,
                "message": "Geçmiş veri yok, tahminler 0 olarak döndürüldü.",
                "data": {"daily_predictions": daily_predictions, "total_predicted_demand": 0.0},
            }

        y = np.array(historical_quantities, dtype=float)
        x = np.arange(len(historical_quantities), dtype=float).reshape(-1, 1)

        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(x)

        model = LinearRegression()
        model.fit(x_scaled, y)

        future_x = np.arange(len(historical_quantities), len(historical_quantities) + days, dtype=float).reshape(-1, 1)
        future_x_scaled = scaler.transform(future_x)
        predictions = np.maximum(model.predict(future_x_scaled), 0.0)

        daily_predictions = [
            {"day": index + 1, "predicted_quantity": float(round(quantity, 2))}
            for index, quantity in enumerate(predictions)
        ]
        total = float(round(float(np.sum(predictions)), 2))
        return {
            "success": True,
            "message": "Talep tahmini başarıyla oluşturuldu.",
            "data": {"daily_predictions": daily_predictions, "total_predicted_demand": total},
        }
