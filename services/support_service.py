"""Destek ile ilgili bot servisleri."""


class SupportService:
    def handle_support_query(self, username: str, message: str) -> str:
        return (
            f"Merhaba {username}, mesaj?n?z? ald?k. "
            "Detayl? destek i?in k?sa s?re i?inde d?n?? yapaca??z."
        )
