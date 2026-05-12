"""Instagram bot orchestrator."""

from __future__ import annotations

import os
import time
import traceback
from dataclasses import dataclass

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from channels.instagram.handlers import MessageHandler
from channels.instagram.login import perform_login
from channels.instagram.message_reader import read_messages
from channels.instagram.message_sender import send_message


@dataclass
class InstagramSettings:
    """Ortam degiskenlerinden okunan ayarlar."""

    username: str
    password: str
    headless: bool
    auto_reply_enabled: bool
    auto_reply_text: str
    manual_login: bool
    manual_login_wait_seconds: int


class InstagramBot:
    """Instagram DM otomasyonu ana sinifi."""

    def __init__(self) -> None:
        self.settings = self._load_settings()
        self.driver = self._build_driver()
        self.handler = MessageHandler()

    def _load_settings(self) -> InstagramSettings:
        if not os.path.exists(".env"):
            raise RuntimeError(".env dosyasi bulunamadi. .env.example dosyasini kopyalayip doldurun.")

        load_dotenv()

        username = os.getenv("INSTAGRAM_USERNAME", "").strip()
        password = os.getenv("INSTAGRAM_PASSWORD", "").strip()
        if not username or not password:
            raise RuntimeError("INSTAGRAM_USERNAME ve INSTAGRAM_PASSWORD zorunludur.")

        headless = os.getenv("INSTAGRAM_HEADLESS", "false").lower() == "true"
        auto_reply_enabled = os.getenv("INSTAGRAM_AUTO_REPLY_ENABLED", "true").lower() == "true"
        auto_reply_text = os.getenv(
            "INSTAGRAM_AUTO_REPLY_TEXT",
            "Merhaba, mesajiniz alindi. En kisa surede donus yapacagiz.",
        )
        manual_login = os.getenv("INSTAGRAM_MANUAL_LOGIN", "false").lower() == "true"
        manual_login_wait_seconds = int(os.getenv("INSTAGRAM_MANUAL_LOGIN_WAIT_SECONDS", "60"))

        return InstagramSettings(
            username=username,
            password=password,
            headless=headless,
            auto_reply_enabled=auto_reply_enabled,
            auto_reply_text=auto_reply_text,
            manual_login=manual_login,
            manual_login_wait_seconds=manual_login_wait_seconds,
        )

    def _build_driver(self) -> webdriver.Chrome:
        options = Options()
        if self.settings.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def run(self) -> None:
        """Login olur, DM okur ve opsiyonel otomatik cevap verir."""
        try:
            perform_login(
                driver=self.driver,
                username=self.settings.username,
                password=self.settings.password,
                manual_login=self.settings.manual_login,
                manual_wait_seconds=self.settings.manual_login_wait_seconds,
            )

            incoming_messages = read_messages(self.driver)
            print(f"Okunan thread sayisi: {len(incoming_messages)}")
            for incoming in incoming_messages:
                reply = self.handler.handle(incoming)
                if self.settings.auto_reply_enabled:
                    send_message(
                        self.driver,
                        incoming.username,
                        reply or self.settings.auto_reply_text,
                        thread_url=incoming.thread_url,
                    )

            # Demo icin tarayiciyi hemen kapatmamak adina kisa bekleme.
            time.sleep(3)
            input("Çıkmak için Enter...")
        except Exception as exc:
            print(f"Instagram bot calisirken hata olustu: {exc}")
            traceback.print_exc()
            input("Çıkmak için Enter...")
        finally:
            pass
