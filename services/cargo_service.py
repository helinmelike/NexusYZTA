"""Kargo ile ilgili bot servisleri."""


class CargoService:
    def handle_cargo_query(self, username: str, message: str) -> str:
        # Burada takip numaras? ayr??t?rma ve API sorgular? eklenebilir.
        return f"Merhaba {username}, kargo durumunuz kontrol ediliyor."
