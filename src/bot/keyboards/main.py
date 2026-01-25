"""Основные клавиатуры для Telegram-бота."""

from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками."""
    keyboard = [
        ["/add 📖", "/list 📚", "/edit ✏️"],
        ["/stats 📊", "/help ❓"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    keyboard = [
        ["/cancel ❌"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def status_keyboard(book_id: str) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для изменения статуса книги."""
    keyboard = [
        [
            InlineKeyboardButton("📖 Хочу прочитать", callback_data=f"change_status:{book_id}:want_to_read"),
            InlineKeyboardButton("📚 Читаю сейчас", callback_data=f"change_status:{book_id}:reading")
        ],
        [
            InlineKeyboardButton("📕 Прочитано", callback_data=f"change_status:{book_id}:read"),
            InlineKeyboardButton("⏸️ Отложено", callback_data=f"change_status:{book_id}:postponed")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def book_actions_keyboard(book_id: str) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для действий с книгой."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Обновить прогресс", callback_data=f"update_progress:{book_id}:0")
        ],
        [
            InlineKeyboardButton("📋 Изменить статус", callback_data=f"select_status:{book_id}"),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_book:{book_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(callback_data: str) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками подтверждения/отмены."""
    keyboard = [
        [
            "/yes ✅",
            "/no ❌"
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def confirm_add_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для подтверждения добавления книги."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_add:confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm_add:cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
