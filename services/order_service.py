"""Sipari? ile ilgili bot servisleri."""


class OrderService:
    def handle_order_query(self, username: str, message: str) -> str:
        # Burada mevcut backend API'lerine ba?lan?labilir.
        return f"Merhaba {username}, sipari?iniz kontrol ediliyor."
