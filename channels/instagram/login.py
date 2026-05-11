"""Instagram manuel giris islemleri."""

from __future__ import annotations

import time

LOGIN_URL = "https://www.instagram.com/accounts/login/"
INBOX_URL = "https://www.instagram.com/direct/inbox/"


def perform_login(
    driver,
    username: str = "",
    password: str = "",
    timeout: int = 25,
    manual_login: bool = True,
    manual_wait_seconds: int = 90,
) -> None:
    """Instagram login sayfasini acar, manuel giris bekler ve DM inbox'a gider."""
    del username, password, timeout, manual_login
    print("MANUEL LOGIN MODU AKTIF")
    print("Lütfen manuel giriş yapın")

    try:
        driver.get(LOGIN_URL)
        time.sleep(manual_wait_seconds)
        driver.get(INBOX_URL)
    except Exception as exc:
        print(f"Manuel login akisi sirasinda hata olustu: {exc}")
        try:
            driver.get(INBOX_URL)
        except Exception as inbox_exc:
            print(f"DM inbox sayfasina gecis basarisiz: {inbox_exc}")
            raise
