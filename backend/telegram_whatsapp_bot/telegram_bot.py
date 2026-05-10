from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Ensure sibling packages (e.g., services) are importable even when this file is run directly.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load environment from project root .env
load_dotenv(dotenv_path=BACKEND_DIR.parent / ".env")

from services.user_service_telegram import get_or_create_customer_from_telegram
from services.support_ticket_service import create_support_ticket

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")


def _build_response_text(customer) -> str:
    return (
        f"Merhaba {customer.full_name},\n"
        "destek için mesajınızı gönderebilirsiniz."
    )


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    if customer:
        text = _build_response_text(customer)
    else:
        text = "Müşteri kaydı oluşturulamadı. Lütfen destek ekibiyle iletişime geçin."
    logger.info("telegram.start user=%s chat_id=%s", customer.id if customer else None, chat_id)
    await update.message.reply_text(text)


async def _message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message_text = update.message.text if update.message else ""
    customer = get_or_create_customer_from_telegram(update.message.from_user)
    if not customer:
        await update.message.reply_text("Müşteri kaydı bulunamadı. /start yazıp tekrar deneyin.")
        return

    if not message_text.strip():
        await update.message.reply_text("Lütfen destek talebinizi yazın.")
        return

    result = create_support_ticket(
        customer_id=customer.id,
        telegram_user_id=chat_id,
        message=message_text,
    )
    if result["success"]:
        await update.message.reply_text("Destek talebiniz alınmıştır. En kısa zamanda yanıtlanacaktır.")
    else:
        await update.message.reply_text(result["message"])


def run_telegram_bot() -> None:
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise RuntimeError("TELEGRAM_BOT_TOKEN bulunamadi. Proje kokundeki .env dosyasini kontrol edin.")
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", _start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _message_handler))
    application.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
