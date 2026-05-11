from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def customer_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📦 Sipariş İşlemleri"],
        ["🚚 Kargo İşlemleri"],
        ["📞 Destek"],
        ["ℹ️ Yardım"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def customer_order_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🔍 Sipariş Sorgula"],
        ["🧠 Sipariş Ver (Web)"],
        ["📋 Siparişlerim"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def customer_cargo_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🚚 Kargo Takibi"],
        ["📍 Kargo Nerede?"],
        ["📅 Tahmini Teslim"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def customer_support_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📦 Siparişim nerede?"],
        ["❌ Sipariş iptali nasıl yapılır?"],
        ["🚚 Kargo gecikti"],
        ["💳 Ödeme sorunu"],
        ["👤 Hesap desteği"],
        ["📝 Diğer (Yazacağım)"],
        ["🌐 Daha fazla destek"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def seller_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📦 Sipariş Yönetimi"],
        ["📊 Stok Yönetimi"],
        ["🚚 Kargo Yönetimi"],
        ["💰 Raporlar"],
        ["ℹ️ Yardım"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def seller_order_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📦 Bugünkü Siparişler"],
        ["🆕 Yeni Siparişler"],
        ["⏳ Hazırlanan Siparişler"],
        ["✅ Teslim Edilenler"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def seller_stock_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📊 Stok Durumu"],
        ["⚠️ Azalan Stoklar"],
        ["➕ Ürün Ekle"],
        ["✏️ Stok Ekle"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def seller_cargo_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🚚 Kargoya Verilecekler"],
        ["📍 Kargo Durumları"],
        ["⬅️ Geri"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def support_feedback_inline_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Cevap yeterli", callback_data="support_ok"),
            InlineKeyboardButton("❌ Cevap yeterli değil", callback_data="support_not_ok"),
        ]]
    )


def confirm_ticket_inline_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🎫 Destek talebi oluştur", callback_data="ticket_create"),
            InlineKeyboardButton("↩️ Destek menüsüne dön", callback_data="ticket_cancel"),
        ]]
    )
