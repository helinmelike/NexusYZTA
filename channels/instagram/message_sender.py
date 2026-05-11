"""DM gonderim altyapisi."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

MESSAGE_INPUT_TEXTAREA = (By.XPATH, "//textarea")
MESSAGE_INPUT_EDITABLE = (By.XPATH, "//div[@contenteditable='true' and @role='textbox']")


def send_message(
    driver,
    username: str,
    message: str,
    timeout: int = 20,
    thread_url: str | None = None,
) -> None:
    """Belirli kullaniciya DM gonderir."""
    wait = WebDriverWait(driver, timeout)

    if thread_url:
        driver.get(thread_url)

    input_box = None
    for locator in (MESSAGE_INPUT_TEXTAREA, MESSAGE_INPUT_EDITABLE):
        try:
            input_box = wait.until(EC.visibility_of_element_located(locator))
            break
        except Exception:
            continue

    if input_box is None:
        raise RuntimeError(f"Mesaj kutusu bulunamadi: {username}")

    input_box.click()
    input_box.send_keys(message)
    input_box.send_keys(Keys.ENTER)
