class EmailService:
    """
    Gecikme bildirimi için e-posta servisi.
    Şu an sadece konsola yazar (stub).
    SMTP entegrasyonu eklenince _send metodu doldurulacak.
    """

    def send_delay_notification(
        self,
        to_email: str,
        order_id: int,
        tracking_number: str,
        days_late: int,
        new_eta: str,
    ) -> bool:
        subject = f"Siparişiniz Gecikti — {tracking_number}"
        body = (
            f"Sayın müşterimiz,\n\n"
            f"{tracking_number} numaralı siparişiniz {days_late} gün gecikmiştir.\n"
            f"Yeni tahmini teslimat tarihi: {new_eta}\n\n"
            f"Özür dileriz."
        )
        return self._send(to_email, subject, body)

    def _send(self, to: str, subject: str, body: str) -> bool:
        # TODO: smtplib veya SendGrid entegrasyonu buraya
        print(f"[EMAIL] To: {to} | Subject: {subject}")
        print(body)
        return True
