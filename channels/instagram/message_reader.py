"""DM okuma altyapisi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

INBOX_URL = "https://www.instagram.com/direct/inbox/"
THREAD_XPATHS = [
    "//a[contains(@href,'/direct/t/')]",
    "//div[@role='main']//a[contains(@href,'/direct/t/')]",
    "//main//a[contains(@href,'/direct/t/')]",
]
THREAD_USERNAME = ".//span"
THREAD_LAST_MESSAGE = ".//span[contains(@class,'x1lliihq') or contains(@class,'_ap3a') or contains(@class,'x1i10hfl')]"
COMMON_DIALOG_BUTTONS = (
    "//button[normalize-space()='Not Now' or normalize-space()='Cancel']",
    "//button[normalize-space()='Simdi Degil' or normalize-space()='Şimdi Değil' or normalize-space()='Vazgec']",
)


@dataclass
class IncomingMessage:
    """Gelen mesaji temsil eder."""

    username: str
    text: str
    thread_url: str | None = None


def read_messages(driver, timeout: int = 20, max_threads: int = 10) -> List[IncomingMessage]:
    """Inbox ekranindan okunabilir thread ozetlerini doner."""
    driver.get(INBOX_URL)
    wait = WebDriverWait(driver, timeout)
    _dismiss_common_dialogs(driver)

    try:
        wait.until(lambda d: _collect_thread_elements(d))
    except TimeoutException:
        print(
            "Inbox threadleri bulunamadi; login tamamlanmamis, mesaj isteklerde olabilir veya UI farkli olabilir. "
            f"url={driver.current_url}"
        )
        return []

    messages: List[IncomingMessage] = []
    threads = _collect_thread_elements(driver)[:max_threads]

    for thread in threads:
        try:
            username = thread.find_element(By.XPATH, THREAD_USERNAME).text.strip()
            preview = ""
            preview_nodes = thread.find_elements(By.XPATH, THREAD_LAST_MESSAGE)
            if preview_nodes:
                preview = preview_nodes[-1].text.strip()
            href = thread.get_attribute("href")
            if not username:
                username = (thread.get_attribute("aria-label") or "").strip()
            if username:
                if not preview:
                    preview = "Merhaba"
                messages.append(IncomingMessage(username=username, text=preview, thread_url=href))
        except Exception:
            # Demo akisinda tek bir thread hatasi tum sureci kesmesin.
            continue

    return messages


def _collect_thread_elements(driver):
    found = []
    for xp in THREAD_XPATHS:
        found.extend(driver.find_elements(By.XPATH, xp))
    # Tekrarlari href ile ayikla
    unique = []
    seen = set()
    for el in found:
        href = el.get_attribute("href")
        key = href or id(el)
        if key in seen:
            continue
        seen.add(key)
        unique.append(el)
    return unique


def _dismiss_common_dialogs(driver) -> None:
    for xp in COMMON_DIALOG_BUTTONS:
        try:
            buttons = driver.find_elements(By.XPATH, xp)
            if buttons:
                buttons[0].click()
        except Exception:
            continue
